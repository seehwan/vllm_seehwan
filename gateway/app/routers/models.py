from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..schemas.model import ModelSwitchRequest, ModelSwitchResponse, ModelStatusResponse
from ..services.model_manager import model_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/models/status", response_model=ModelStatusResponse)
async def get_model_status():
    """현재 모델 상태 조회"""
    try:
        return await model_manager.get_status()
    except Exception as e:
        logger.error(f"모델 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="모델 상태 조회 실패")


@router.get("/models/profiles")
async def get_model_profiles():
    """사용 가능한 모델 프로파일 목록 조회"""
    try:
        return {
            "profiles": model_manager.profiles,
            "current_profile": model_manager.current_profile
        }
    except Exception as e:
        logger.error(f"프로파일 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="프로파일 조회 실패")


@router.post("/models/switch", response_model=ModelSwitchResponse)
async def switch_model(request: ModelSwitchRequest, background_tasks: BackgroundTasks):
    """모델 전환 (백그라운드에서 실행)"""
    try:
        profile_id = request.profile_id
        
        if profile_id not in model_manager.profiles:
            raise HTTPException(
                status_code=404, 
                detail=f"프로파일 '{profile_id}'를 찾을 수 없습니다."
            )
        
        if model_manager.current_profile == profile_id and model_manager.status == "running":
            return ModelSwitchResponse(
                success=True,
                message=f"이미 '{profile_id}' 모델이 실행 중입니다.",
                current_profile=profile_id
            )
        
        # 백그라운드에서 모델 전환 실행
        background_tasks.add_task(model_manager.switch_model, profile_id)
        
        return ModelSwitchResponse(
            success=True,
            message=f"모델 전환을 시작합니다: {model_manager.profiles[profile_id].name}",
            current_profile=model_manager.current_profile,
            switching_to=profile_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 전환 요청 실패: {e}")
        raise HTTPException(status_code=500, detail="모델 전환 요청 실패")


@router.get("/models/hardware-recommendations")
async def get_hardware_recommendations():
    """현재 하드웨어에 맞는 모델 추천"""
    try:
        hardware_info = await model_manager._get_hardware_info()
        available_vram = hardware_info.get("available_vram_gb", 0)
        gpu_count = hardware_info.get("gpu_count", 0)
        
        recommendations = {
            "current_hardware": hardware_info,
            "recommended_profiles": [],
            "compatible_profiles": [],
            "incompatible_profiles": []
        }
        
        for profile_id, profile in model_manager.profiles.items():
            compatibility = model_manager._check_hardware_compatibility(profile, hardware_info)
            
            profile_info = {
                "profile_id": profile_id,
                "name": profile.name,
                "description": profile.description,
                "compatibility": compatibility
            }
            
            if compatibility["compatible"]:
                recommendations["compatible_profiles"].append(profile_info)
                
                # RTX 3090 기준 추천 로직
                hardware_reqs = getattr(profile, 'hardware_requirements', {})
                recommended_vram = hardware_reqs.get('recommended_vram_gb', 0)
                
                if recommended_vram <= available_vram:
                    recommendations["recommended_profiles"].append(profile_info)
            else:
                recommendations["incompatible_profiles"].append(profile_info)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"하드웨어 추천 실패: {e}")
        raise HTTPException(status_code=500, detail="하드웨어 추천 조회 실패")


@router.post("/models/reload")
async def reload_profiles():
    """프로파일 설정 재로드"""
    try:
        model_manager.load_profiles()
        return {
            "success": True,
            "message": "프로파일이 성공적으로 재로드되었습니다.",
            "profiles": model_manager.profiles
        }
    except Exception as e:
        logger.error(f"프로파일 재로드 실패: {e}")
        raise HTTPException(status_code=500, detail="프로파일 재로드 실패")
