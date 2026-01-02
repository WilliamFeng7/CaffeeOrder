from pydantic_settings import BaseSettings

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
    # 这里为了开发方便硬编码了一个哈希值。
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    
    # 加密算法
    ALGORITHM: str = "HS256"
    
    # Access Token 过期时间 (分钟) - 默认 7 天
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    class Config:
        # 区分大小写
        case_sensitive = True

settings = Settings()
