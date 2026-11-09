"""项目管理 CLI。

职责：提供需**显式执行**的一次性运维命令。目前只有 `create-admin`——创建首个管理员。

约束：
- **不经过 HTTP 层**：直接用 `async_session_factory`；**不 import `app.main`**
  （它模块级执行 `create_app()`，会注册异常处理器、中间件与 lifespan，对 CLI 毫无必要）。
- 密码在运行时**交互输入**、不回显；经 `app/core/security.py` 的 Argon2id 哈希后入库，
  **任何地方都不打印明文**。
- 库里已存在**任意** `ADMIN` 时明确拒绝并退出：不重置凭据、不改动现有用户的角色
  （v1.0项目文档.md 第 9.1 节）。
- 事务由本模块**显式 commit**；不要依赖任何自动提交。

"""

import argparse
import asyncio
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.common.enums import SystemRole, UserStatus
from app.core.security import MIN_PASSWORD_LENGTH, hash_password
from app.infrastructure.database.session import (
    async_session_factory,
    engine,
)
from app.modules.users.models import User


async def create_admin(args: argparse.Namespace) -> None:
    """创建首个系统管理员"""
    try:
        async with async_session_factory() as session:
            # 执行查询，获取第一列的一个标量结果；查到管理员就返回其 ID，查不到则返回 None
            existing_admin_id = await session.scalar(
                select(User.id).where(User.system_role == SystemRole.ADMIN).limit(1)
            )

            if existing_admin_id is not None:
                print("系统中已经存在管理员，未创建新用户")
                raise SystemExit(1)

            # 交互基本信息
            username = input("用户名:").strip()
            email = input("邮箱地址:").strip()
            display_name = input("名称:").strip()

            if not username or not email or not display_name:
                print("创建失败：用户名、邮箱和显示名称不能为空")
                raise SystemExit(1)

            # 输入密码
            password = getpass("密码:")
            confirm_password = getpass("再次确认密码：")

            if password != confirm_password:
                print("创建失败：两次输入的密码不一致")
                raise SystemExit(1)

            if len(password) < MIN_PASSWORD_LENGTH:
                print(f"创建失败：密码长度不能少于 {MIN_PASSWORD_LENGTH} 个字符")
                raise SystemExit(1)

            # 构造用户对象
            user = User(
                user_code=username,
                username=username,
                email=email,
                display_name=display_name,
                password_hash=hash_password(password),
                system_role=SystemRole.ADMIN,
                status=UserStatus.ACTIVE,
                must_change_password=False,
            )

            # 将对象加入当前会话
            session.add(user)

            # 提交事务，处理数据库完整性约束冲突
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                print("创建失败：用户名或邮箱可能已存在")
                raise SystemExit(1) from None

            print("管理员创建成功")

    finally:
        # 7. 释放数据库引擎资源
        await engine.dispose()


async def main() -> None:
    # 创建子命令并通过关联处理函数
    parser = argparse.ArgumentParser(description="项目管理命令行工具")
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # 为 create_admin 命令创建解析器
    parser_create_admin = subparsers.add_parser(
        "create-admin",
        help="创建首个系统管理员",
    )
    parser_create_admin.set_defaults(func=create_admin)

    # 解析参数并调用所选的任意函数
    args = parser.parse_args()
    await args.func(args)


if __name__ == "__main__":
    asyncio.run(main())
