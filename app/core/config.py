"""统一配置系统（pydantic-settings）。

职责：从环境变量读取全部配置，并在**启动时校验**；缺失或非法应直接启动失败并给出明确提示。

约束：
- 不得在代码中硬编码地址、端口、密码或模型名称（README 第 11 节设计要求 7）。
- 字段名、环境变量名与 docker-compose.yml 必须保持一致（同节要求 8）。

字段清单见 README 第 11 节与 .env.example。
"""

from functools import lru_cache
from typing import Literal, Self

from pydantic import ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    # =========================
    # 1. 应用配置
    # =========================
    app_name: str = "StudyLab"
    app_env: Literal[
        "development",
        "production",
    ] = "development"

    debug: bool = False
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # =========================
    # 2. 数据库配置
    # =========================
    database_url: str
    postgres_password: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    # =========================
    # 3. 告诉 pydantic-settings
    #    配置从哪里读取
    # =========================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # =========================
    # 4. 字段级校验
    # =========================
    @field_validator(
        "database_url",
        "postgres_password",
    )
    @classmethod
    def reject_change_me(
        cls,
        value: str,
        info: ValidationInfo,
    ) -> str:
        if value == "CHANGE_ME":
            raise ValueError(f"{info.field_name} 还是模板占位值，请填写真实配置")
        return value

    # =========================
    # 5. 跨字段校验
    # =========================
    @model_validator(mode="after")
    def validate_database_password(self) -> Self:
        url = make_url(self.database_url)

        if url.password is None:
            raise ValueError("密码没有")
        if url.password != self.postgres_password:
            raise ValueError("密码找不到")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
