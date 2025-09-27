import asyncio
import logging
import os
import subprocess
from typing import Optional
import aiohttp
import json

import yaml

from ..schemas.model import ModelProfile, ModelStatusResponse

logger = logging.getLogger(__name__)


class VLLMModelManager:
    """vLLM 모델 관리 서비스"""

    def __init__(self, profiles_path: str = "/app/model_profiles.yml"):
        self.profiles_path = profiles_path
        self.current_profile: Optional[str] = None
        self.status = "stopped"
        self.profiles: dict[str, ModelProfile] = {}
        self.hardware_profiles: dict = {}
        self.vllm_process: Optional[subprocess.Popen] = None
        self._cached_hardware_info: Optional[dict] = None  # 캐시된 하드웨어 정보
        self.vllm_base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        self.load_profiles()

    def load_profiles(self):
        """프로파일 설정 파일 로드"""
        try:
            if os.path.exists(self.profiles_path):
                with open(self.profiles_path, encoding='utf-8') as f:
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
        logger.info("=== get_status 함수 호출됨 ===")
        # vLLM 서버 실제 상태 확인
        await self._check_vllm_status()
        
        # 하드웨어 정보 추가 - 실패시 예외 발생
        try:
            hardware_info = await self._get_hardware_info()
        except RuntimeError as e:
            logger.error(f"하드웨어 정보 조회 실패로 인한 서비스 중단: {e}")
            # 서비스 상태를 error로 설정
            self.status = "error"
            return ModelStatusResponse(
                current_profile=self.current_profile,
                status="error",
                available_profiles=self.profiles,
                message=f"서비스 오류: {str(e)}",
                hardware_info=None
            )

        return ModelStatusResponse(
            current_profile=self.current_profile,
            status=self.status,
            available_profiles=self.profiles,
            message=f"현재 {'실행 중' if self.status == 'running' else '정지됨'}",
            hardware_info=hardware_info
        )

    async def _get_hardware_info(self) -> dict:
        """하드웨어 정보 조회 - 기본 GPU 정보 반환"""
        logger.info("기본 GPU 정보 사용 (nvidia-smi 의존성 제거)")
        
        # 기본 GPU 정보 (RTX 3090 24GB x 2)
        hardware_info = {
            "gpus": [
                {
                    "name": "NVIDIA GeForce RTX 3090",
                    "memory_total_mb": 24576,  # 24GB in MB
                    "memory_used_mb": 0,
                    "memory_free_mb": 24576
                },
                {
                    "name": "NVIDIA GeForce RTX 3090", 
                    "memory_total_mb": 24576,  # 24GB in MB
                    "memory_used_mb": 0,
                    "memory_free_mb": 24576
                }
            ],
            "gpu_count": 2,
            "total_vram_gb": 48.0,  # 48GB total
            "available_vram_gb": 48.0  # 48GB available
        }
        
        # 결과를 캐시
        self._cached_hardware_info = hardware_info
        logger.info("기본 GPU 정보 설정 완료: 2개 GPU, 48GB VRAM")
        return hardware_info

    async def _check_vllm_status(self):
        """vLLM 서버 실제 상태 확인"""
        await self._update_status_from_vllm()

    async def switch_model(self, profile_id: str) -> bool:
        """모델 전환"""
        if profile_id not in self.profiles:
            raise ValueError(f"프로파일 '{profile_id}'를 찾을 수 없습니다.")

        # 하드웨어 호환성 검증
        profile = self.profiles[profile_id]
        
        try:
            hardware_info = await self._get_hardware_info()
        except RuntimeError as e:
            logger.error(f"하드웨어 정보 조회 실패로 인한 모델 전환 중단: {e}")
            raise ValueError(f"하드웨어 정보 조회 실패: {str(e)}")

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

    def _check_hardware_compatibility(self, profile: ModelProfile, hardware_info: dict) -> dict:
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

    async def _check_vllm_connection(self) -> bool:
        """vLLM 서버 연결 상태 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.vllm_base_url}/models", timeout=5) as response:
                    if response.status == 200:
                        logger.info("vLLM 서버 연결 성공")
                        return True
                    else:
                        logger.warning(f"vLLM 서버 응답 오류: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"vLLM 서버 연결 실패: {e}")
            return False

    async def _get_vllm_models(self) -> list[dict]:
        """vLLM 서버에서 실제 모델 목록 가져오기"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.vllm_base_url}/models", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("data", [])
                        logger.info(f"vLLM에서 {len(models)}개 모델 발견")
                        return models
                    else:
                        logger.error(f"vLLM 모델 목록 조회 실패: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"vLLM 모델 목록 조회 오류: {e}")
            return []

    async def _update_status_from_vllm(self):
        """vLLM 서버 상태를 기반으로 상태 업데이트"""
        try:
            is_connected = await self._check_vllm_connection()
            if is_connected:
                models = await self._get_vllm_models()
                if models:
                    self.status = "running"
                    # 실제 실행 중인 모델을 동적으로 프로파일로 생성
                    await self._create_profiles_from_vllm_models(models)
                    
                    # 첫 번째 모델을 current_profile로 설정
                    if models and not self.current_profile:
                        model_id = models[0].get("id", "")
                        # 동적으로 생성된 프로파일에서 찾기
                        for profile_id, profile in self.profiles.items():
                            if model_id == profile.model_id:
                                self.current_profile = profile_id
                                break
                    logger.info(f"vLLM 상태: 실행 중, 모델: {len(models)}개, 프로파일: {len(self.profiles)}개")
                else:
                    self.status = "stopped"
                    logger.info("vLLM 상태: 정지됨 (모델 없음)")
            else:
                self.status = "stopped"
                logger.info("vLLM 상태: 정지됨 (연결 실패)")
        except Exception as e:
            logger.error(f"vLLM 상태 업데이트 실패: {e}")
            self.status = "stopped"

    async def _create_profiles_from_vllm_models(self, models: list[dict]):
        """vLLM에서 가져온 실제 모델들을 프로파일로 변환"""
        try:
            for model in models:
                model_id = model.get("id", "")
                if not model_id:
                    continue
                
                # 프로파일 ID 생성 (모델 ID에서 안전한 ID 추출)
                profile_id = model_id.replace("/", "-").replace("_", "-").lower()
                
                # 이미 존재하는 프로파일이면 건너뛰기
                if profile_id in self.profiles:
                    continue
                
                # 모델 이름 추출 (ID에서 마지막 부분)
                model_name = model_id.split("/")[-1].replace("-", " ").title()
                
                # 동적으로 프로파일 생성 (실제 vLLM 모델 ID 사용)
                profile = ModelProfile(
                    name=model_name,
                    model_id=model_id,  # 실제 vLLM 모델 ID 그대로 사용
                    description=f"실행 중인 모델: {model_name}",
                    max_model_len=model.get("max_model_len", 4096),
                    tensor_parallel_size=1,  # 기본값
                    gpu_memory_utilization=0.8,  # 기본값
                    dtype="float16",  # 기본값
                    swap_space=4,  # 기본값
                    hardware_requirements={
                        "min_vram_gb": 8,
                        "recommended_vram_gb": 16,
                        "min_gpus": 1
                    }
                )
                
                self.profiles[profile_id] = profile
                logger.info(f"동적 프로파일 생성: {profile_id} -> {model_name}")
                
        except Exception as e:
            logger.error(f"프로파일 생성 실패: {e}")

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
                    response = await client.get("http://vllm-server:8000/v1/models", timeout=5.0)
                    if response.status_code == 200:
                        logger.info("vLLM 서버 준비 완료")
                        return
            except:
                pass

            await asyncio.sleep(5)

        raise TimeoutError("vLLM 서버 준비 시간 초과")


# 전역 모델 매니저 인스턴스
model_manager = VLLMModelManager()
