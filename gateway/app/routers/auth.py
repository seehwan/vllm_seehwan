from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog
from ..config import settings

router = APIRouter()
logger = structlog.get_logger()
security = HTTPBearer()


@router.post("/login")
async def login():
    """로그인 (현재는 더미 구현)"""
    return {
        "access_token": "dummy_token_for_development",
        "token_type": "bearer"
    }


@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """현재 사용자 정보 조회"""
    # 실제 구현에서는 JWT 토큰을 검증해야 함
    return {
        "user_id": "user123",
        "email": "user@example.com"
    }


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT 토큰 검증 (현재는 더미 구현)"""
    # 실제 구현에서는 JWT 디코딩 및 검증
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return {"user_id": "user123"}
