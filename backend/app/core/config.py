import secrets
import os
import warnings
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    系统配置类 (System Configuration)
    从环境变量中读取配置，如果不存在则使用默认值。
    """
    # 项目名称
    PROJECT_NAME: str = "School Coffee System"
    # API 路径前缀
    API_V1_STR: str = "/api/v1"
    
    # 密钥 (Security Key)
    # 警告：在生产环境中，必须保持此密钥的机密性！建议通过环境变量 SECRET_KEY 注入。
    # Sentinel Fix: Removed hardcoded secret. Now generates a random key if not provided.
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    
    # 加密算法
    ALGORITHM: str = "HS256"
    
    # Access Token 过期时间 (分钟) - 默认 7 天
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Pydantic V2 Configuration
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Check if SECRET_KEY was loaded from environment
        if not os.getenv("SECRET_KEY"):
            warnings.warn(
                "SECRET_KEY not set in environment. Using generated temporary key. "
                "Sessions will not persist across restarts.",
                UserWarning
            )

settings = Settings()
