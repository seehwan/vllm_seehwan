from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog

from .config import settings
from .routers import chat, auth, health, conversations, models
from .database import init_db
from .middleware import LoggingMiddleware, RateLimitMiddleware

# 로거 설정
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 시작 시
    logger.info("🚀 vLLM Gateway 시작...")
    await init_db()
    logger.info("✅ 데이터베이스 초기화 완료")
    
    yield
    
    # 종료 시
    logger.info("👋 vLLM Gateway 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="vLLM Chat Gateway API",
    description="vLLM 기반 챗봇 서비스를 위한 FastAPI 게이트웨이",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 설정
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 커스텀 미들웨어
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# 라우터 등록
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
app.include_router(models.router, prefix="/api", tags=["Models"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "vLLM Chat Gateway",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.DEBUG else None,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """글로벌 예외 처리"""
    logger.error("Unhandled exception", exception=str(exc), path=request.url.path)
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )
