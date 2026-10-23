"""密码哈希与 access token 的签发 / 解析。

职责：提供密码哈希与校验、access token 的签发与解析，供认证模块与依赖注入调用。

约束：
- **不碰数据库**：本模块是纯计算。refresh token 的生成、存储与吊销归 `app/modules/auth`。
- 密钥与算法一律取自 `get_settings()`，不得硬编码（README 第 11 节设计要求 7）。
  本项目**只有 access token 是 JWT**——refresh token 是 opaque 随机串、不签名，
  故只有 `JWT_ACCESS_SECRET` 一个密钥（v1.0项目文档.md 第 2.3 / 5.2 节）。
- `PasswordHash` 实例**模块级只建一次**：每次新建都会重新推导 Argon2 参数，开销很大。
- `jwt.decode` 必须**显式限定算法**为配置中的那一个——这是防算法混淆攻击的关键。
"""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException

password_hash = PasswordHash.recommended()

# 密码策略：注册与 CLI 建管理员共用。12 是 NIST 最低线(8)与本项目无登录频控之间的折中；
# 登录不校验此值，只在校验注册与改密时生效。
MIN_PASSWORD_LENGTH=12


def hash_password(plain) -> str:
    return password_hash.hash(plain)


def verify_password(plain, hash) -> bool:
    return password_hash.verify(plain, hash)


# 接收一个用户标识，生成一个带有过期时间的 JWT 字符串，并返回它
def create_access_token(subject: str) -> str:
    settings = get_settings()

    # 计算令牌的过期时间
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    # 构造 JWT payload
    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_access_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token) -> dict:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_access_secret,
            algorithms=[settings.jwt_algorithm],
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("令牌已过期")

    except jwt.InvalidTokenError:
        raise UnauthorizedException("令牌无效")
