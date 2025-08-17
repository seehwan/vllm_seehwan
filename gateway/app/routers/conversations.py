from fastapi import APIRouter, Depends, HTTPException
import structlog
from ..routers.auth import verify_token
from typing import List, Dict, Any

router = APIRouter()
logger = structlog.get_logger()


@router.get("/conversations")
async def get_conversations(
    user = Depends(verify_token)
):
    """사용자의 대화 목록 조회"""
    # 현재는 더미 데이터 반환
    return {
        "conversations": [
            {
                "id": "conv1",
                "title": "Python 코딩 질문",
                "created_at": "2025-01-15T10:00:00Z",
                "message_count": 5
            },
            {
                "id": "conv2", 
                "title": "FastAPI 개발",
                "created_at": "2025-01-14T15:30:00Z",
                "message_count": 12
            }
        ]
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user = Depends(verify_token)
):
    """특정 대화 상세 조회"""
    # 현재는 더미 데이터 반환
    return {
        "id": conversation_id,
        "title": "대화 제목",
        "created_at": "2025-01-15T10:00:00Z",
        "messages": [
            {
                "role": "user",
                "content": "안녕하세요!",
                "timestamp": "2025-01-15T10:00:00Z"
            },
            {
                "role": "assistant", 
                "content": "안녕하세요! 무엇을 도와드릴까요?",
                "timestamp": "2025-01-15T10:00:05Z"
            }
        ]
    }


@router.post("/conversations")
async def create_conversation(
    request: Dict[str, Any],
    user = Depends(verify_token)
):
    """새 대화 생성"""
    return {
        "id": "new_conv_123",
        "title": request.get("title", "새 대화"),
        "created_at": "2025-01-15T12:00:00Z"
    }
