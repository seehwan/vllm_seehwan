
from pydantic_settings import BaseSettings
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

    # CORS 설정 - 환경 변수에서 직접 가져옴
    ALLOWED_HOSTS: list[str] = ["*"]
    
    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins를 리스트로 변환"""
        return ["http://localhost:3000", "http://localhost:80", "http://localhost"]

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
        env_file = "../.env.local"  # 프로젝트 루트의 .env.local 파일 사용
        case_sensitive = True
        # CORS_ORIGINS 필드는 환경 변수에서 제외
        env_ignore = {'CORS_ORIGINS'}


# 설정 인스턴스 생성
settings = Settings()
