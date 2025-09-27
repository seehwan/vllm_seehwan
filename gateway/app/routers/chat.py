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
        logger.info(f"채팅 요청 받음: stream={request.get('stream', False)}")
        
        # vLLM API로 요청 전달
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.VLLM_BASE_URL}/chat/completions",
                json=request,
                headers={"Content-Type": "application/json"},
                timeout=60.0
            )
            
            logger.info(f"vLLM 응답 상태: {response.status_code}, content-type: {response.headers.get('content-type', 'None')}")
            
            # 스트리밍 요청인지 확인
            if request.get("stream", False):
                logger.info("스트리밍 응답 처리 시작")
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
                logger.info("일반 JSON 응답 처리 시작")
                # 일반 JSON 응답
                response_text = await response.aread()
                logger.info(f"응답 텍스트 길이: {len(response_text)}")
                if response_text:
                    try:
                        return response.json()
                    except Exception as json_error:
                        logger.error(f"JSON 파싱 오류: {json_error}")
                        logger.error(f"응답 텍스트: {response_text.decode('utf-8', errors='ignore')[:500]}")
                        raise HTTPException(status_code=502, detail=f"vLLM 응답 파싱 실패: {str(json_error)}")
                else:
                    raise HTTPException(status_code=502, detail="vLLM 서버에서 빈 응답을 받았습니다")
                
    except httpx.RequestError as e:
        logger.error(f"vLLM 연결 오류: {e}")
        raise HTTPException(status_code=502, detail="vLLM 서버 연결 실패")
    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류 발생: {str(e)}")
