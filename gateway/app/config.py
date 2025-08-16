from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    APP_NAME: str = "vLLM Chat Gateway"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # vLLM 설정
    VLLM_BASE_URL: str = "http://localhost:8000/v1"
    VLLM_API_KEY: str = ""
    
    # 보안 설정
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    
    # CORS 설정
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/chatdb"
    
    # Redis 설정
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 레이트 리밋 설정
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1시간
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    
    # 모니터링 설정
    PROMETHEUS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 설정 인스턴스 생성
settings = Settings()
