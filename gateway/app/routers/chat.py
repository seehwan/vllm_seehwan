from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import structlog
import httpx
from ..config import settings
from ..routers.auth import verify_token
from typing import List, Dict, Any

router = APIRouter()
logger = structlog.get_logger()


@router.post("/chat")
async def chat_completion(
    request: Dict[str, Any],
    user = Depends(verify_token)
):
    """채팅 완성 API - vLLM으로 프록시"""
    try:
        # vLLM API로 요청 전달
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.VLLM_BASE_URL}/chat/completions",
                json=request,
                headers={"Content-Type": "application/json"},
                timeout=60.0
            )
            
            if response.headers.get("content-type", "").startswith("text/plain"):
                # SSE 스트리밍 응답
                return StreamingResponse(
                    response.aiter_text(),
                    media_type="text/plain",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                    }
                )
            else:
                # 일반 JSON 응답
                return response.json()
                
    except httpx.RequestError as e:
        logger.error(f"vLLM 연결 오류: {e}")
        raise HTTPException(status_code=502, detail="vLLM 서버 연결 실패")
    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}")
        raise HTTPException(status_code=500, detail="채팅 처리 중 오류 발생")
