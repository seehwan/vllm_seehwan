from fastapi import APIRouter
import structlog
from ..config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "vLLM Chat Gateway",
        "version": "1.0.0"
    }


@router.get("/health/ready")
async def readiness_check():
    """준비 상태 확인"""
    # 여기서 vLLM 연결, 데이터베이스 연결 등을 확인할 수 있음
    return {
        "status": "ready",
        "vllm_base_url": settings.VLLM_BASE_URL
    }
