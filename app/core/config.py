"""应用配置：全部走环境变量，本地默认 SQLite，开箱即跑。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "LogShield API"
    # 默认 SQLite 文件库；切 MySQL 只需改环境变量，例如：
    # DATABASE_URL=mysql+pymysql://user:pass@db:3306/logshield
    database_url: str = "sqlite:///./logshield.db"
    secret_key: str = "dev-secret-change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24


settings = Settings()
