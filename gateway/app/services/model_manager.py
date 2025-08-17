import yaml
import asyncio
import subprocess
import logging
import os
import json
from typing import Dict, Optional
from pathlib import Path

from ..schemas.model import ModelProfile, ModelStatusResponse


logger = logging.getLogger(__name__)


class VLLMModelManager:
    """vLLM 모델 관리 서비스"""
    
    def __init__(self, profiles_path: str = "/app/model_profiles.yml"):
        self.profiles_path = profiles_path
        self.current_profile: Optional[str] = None
        self.status = "stopped"
        self.profiles: Dict[str, ModelProfile] = {}
        self.hardware_profiles: Dict = {}
        self.vllm_process: Optional[subprocess.Popen] = None
        self.load_profiles()
    
    def load_profiles(self):
        """프로파일 설정 파일 로드"""
        try:
            if os.path.exists(self.profiles_path):
                with open(self.profiles_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                for profile_id, profile_data in config.get('model_profiles', {}).items():
                    self.profiles[profile_id] = ModelProfile(**profile_data)
                    
                # 하드웨어 프로파일 로드
                self.hardware_profiles = config.get('hardware_profiles', {})
                    
                # 기본 프로파일 설정
                default_profile = config.get('default_profile')
                if default_profile and default_profile in self.profiles:
                    self.current_profile = default_profile
                    
        except Exception as e:
            logger.error(f"프로파일 로드 실패: {e}")
            # 기본 프로파일 생성
            self.profiles["default"] = ModelProfile(
                name="Default Model",
                model_id="deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
                description="기본 모델",
                max_model_len=8192,
                tensor_parallel_size=2,
                gpu_memory_utilization=0.85
            )
            self.current_profile = "default"
            self.hardware_profiles = {}
    
    async def get_status(self) -> ModelStatusResponse:
        """현재 모델 상태 반환"""
        # 하드웨어 정보 추가
        hardware_info = await self._get_hardware_info()
        
        return ModelStatusResponse(
            current_profile=self.current_profile,
            status=self.status,
            available_profiles=self.profiles,
            message=f"현재 {'실행 중' if self.status == 'running' else '정지됨'}",
            hardware_info=hardware_info
        )
    
    async def _get_hardware_info(self) -> Dict:
        """하드웨어 정보 조회"""
        try:
            # nvidia-smi로 GPU 정보 조회
            process = await asyncio.create_subprocess_exec(
                "nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free", 
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                gpus = []
                for line in stdout.decode().strip().split('\n'):
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 4:
                            gpus.append({
                                "name": parts[0],
                                "memory_total_mb": int(parts[1]),
                                "memory_used_mb": int(parts[2]),
                                "memory_free_mb": int(parts[3])
                            })
                
                return {
                    "gpus": gpus,
                    "gpu_count": len(gpus),
                    "total_vram_gb": sum(gpu["memory_total_mb"] for gpu in gpus) / 1024,
                    "available_vram_gb": sum(gpu["memory_free_mb"] for gpu in gpus) / 1024
                }
        except Exception as e:
            logger.error(f"하드웨어 정보 조회 실패: {e}")
            
        return {
            "gpus": [],
            "gpu_count": 0,
            "total_vram_gb": 0,
            "available_vram_gb": 0
        }
    
    async def switch_model(self, profile_id: str) -> bool:
        """모델 전환"""
        if profile_id not in self.profiles:
            raise ValueError(f"프로파일 '{profile_id}'를 찾을 수 없습니다.")
        
        # 하드웨어 호환성 검증
        profile = self.profiles[profile_id]
        hardware_info = await self._get_hardware_info()
        
        compatibility_check = self._check_hardware_compatibility(profile, hardware_info)
        if not compatibility_check["compatible"]:
            raise ValueError(f"하드웨어 호환성 문제: {compatibility_check['message']}")
        
        try:
            self.status = "switching"
            logger.info(f"모델 전환 시작: {profile_id}")
            
            # 기존 vLLM 프로세스 종료
            await self._stop_vllm()
            
            # 새 모델로 vLLM 시작
            success = await self._start_vllm(profile_id)
            
            if success:
                self.current_profile = profile_id
                self.status = "running"
                logger.info(f"모델 전환 완료: {profile_id}")
                return True
            else:
                self.status = "error"
                logger.error(f"모델 전환 실패: {profile_id}")
                return False
                
        except Exception as e:
            self.status = "error"
            logger.error(f"모델 전환 중 오류: {e}")
            return False
    
    def _check_hardware_compatibility(self, profile: ModelProfile, hardware_info: Dict) -> Dict:
        """하드웨어 호환성 검증"""
        gpu_count = hardware_info.get("gpu_count", 0)
        available_vram_gb = hardware_info.get("available_vram_gb", 0)
        
        # profile에서 하드웨어 요구사항 확인 (있는 경우)
        hardware_reqs = getattr(profile, 'hardware_requirements', {})
        
        min_vram = hardware_reqs.get('min_vram_gb', 8)  # 기본값
        min_gpus = hardware_reqs.get('min_gpus', 1)
        
        if gpu_count < min_gpus:
            return {
                "compatible": False,
                "message": f"최소 {min_gpus}개 GPU 필요 (현재 {gpu_count}개)"
            }
        
        if available_vram_gb < min_vram:
            return {
                "compatible": False,
                "message": f"최소 {min_vram}GB VRAM 필요 (현재 {available_vram_gb:.1f}GB 사용 가능)"
            }
        
        # tensor_parallel_size와 GPU 수 확인
        if profile.tensor_parallel_size > gpu_count:
            return {
                "compatible": False,
                "message": f"모델의 tensor_parallel_size({profile.tensor_parallel_size})가 사용 가능한 GPU 수({gpu_count})보다 큽니다"
            }
        
        return {
            "compatible": True,
            "message": "하드웨어 호환성 확인됨"
        }
    
    async def _stop_vllm(self):
        """vLLM 프로세스 종료"""
        try:
            # Docker 컨테이너 중지
            process = await asyncio.create_subprocess_exec(
                "docker", "compose", "stop", "vllm",
                cwd="/app",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.wait()
            
            # GPU 메모리 정리
            await asyncio.sleep(5)  # GPU 메모리 해제 대기
            
        except Exception as e:
            logger.error(f"vLLM 종료 실패: {e}")
    
    async def _start_vllm(self, profile_id: str) -> bool:
        """새 프로파일로 vLLM 시작"""
        try:
            profile = self.profiles[profile_id]
            
            # 환경 변수 설정
            env = os.environ.copy()
            env.update({
                "MODEL_ID": profile.model_id,
                "VLLM_MAXLEN": str(profile.max_model_len),
                "VLLM_TP": str(profile.tensor_parallel_size),
                "VLLM_UTIL": str(profile.gpu_memory_utilization),
                "VLLM_SWAP_SPACE": str(profile.swap_space),
                "VLLM_DTYPE": profile.dtype
            })
            
            # Docker 컨테이너 시작
            process = await asyncio.create_subprocess_exec(
                "docker", "compose", "up", "-d", "vllm",
                cwd="/app",
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.wait()
            
            if process.returncode == 0:
                # vLLM 준비 완료 대기
                await self._wait_for_vllm_ready()
                return True
            else:
                logger.error(f"vLLM 시작 실패: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"vLLM 시작 중 오류: {e}")
            return False
    
    async def _wait_for_vllm_ready(self, timeout: int = 300):
        """vLLM 서버 준비 완료 대기"""
        import httpx
        
        for _ in range(timeout // 5):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8000/v1/models", timeout=5.0)
                    if response.status_code == 200:
                        logger.info("vLLM 서버 준비 완료")
                        return
            except:
                pass
            
            await asyncio.sleep(5)
        
        raise TimeoutError("vLLM 서버 준비 시간 초과")


# 전역 모델 매니저 인스턴스
model_manager = VLLMModelManager()
