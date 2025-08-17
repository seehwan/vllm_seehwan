from typing import Any, Optional

from pydantic import BaseModel


class ModelProfile(BaseModel):
    """모델 프로파일 스키마"""
    name: str
    model_id: str
    description: str
    max_model_len: int = 4096
    tensor_parallel_size: int = 1
    gpu_memory_utilization: float = 0.85
    dtype: str = "float16"
    swap_space: int = 4
    hardware_requirements: Optional[dict[str, Any]] = None


class HardwareInfo(BaseModel):
    """하드웨어 정보 스키마"""
    gpus: list[dict[str, Any]]
    gpu_count: int
    total_vram_gb: float
    available_vram_gb: float


class ModelSwitchRequest(BaseModel):
    """모델 전환 요청 스키마"""
    profile_id: str


class ModelSwitchResponse(BaseModel):
    """모델 전환 응답 스키마"""
    success: bool
    message: str
    current_profile: Optional[str] = None
    switching_to: Optional[str] = None


class ModelStatusResponse(BaseModel):
    """모델 상태 응답 스키마"""
    current_profile: Optional[str]
    status: str  # "running", "switching", "stopped", "error"
    available_profiles: dict[str, ModelProfile]
    message: Optional[str] = None
    hardware_info: Optional[dict[str, Any]] = None
