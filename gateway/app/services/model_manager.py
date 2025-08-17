import asyncio
import logging
import os
import subprocess
from typing import Optional

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
        """하드웨어 정보 조회 - 호스트의 nvidia-smi 사용"""
        # 먼저 직접 nvidia-smi 실행 시도 (컨테이너 내에서 가능하도록 설정됨)
        try:
            logger.info("직접 nvidia-smi 실행 시도")
            process = await asyncio.create_subprocess_exec(
                "nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info("직접 nvidia-smi 실행 성공")
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

                hardware_info = {
                    "gpus": gpus,
                    "gpu_count": len(gpus),
                    "total_vram_gb": sum(gpu["memory_total_mb"] for gpu in gpus) / 1024,
                    "available_vram_gb": sum(gpu["memory_free_mb"] for gpu in gpus) / 1024
                }
                
                # 성공한 결과를 캐시
                self._cached_hardware_info = hardware_info
                logger.info(f"하드웨어 정보 성공적으로 조회: {len(gpus)}개 GPU")
                return hardware_info
            else:
                logger.warning(f"직접 nvidia-smi 실행 실패 - returncode: {process.returncode}, stderr: {stderr.decode()}")
        except Exception as e:
            logger.warning(f"직접 nvidia-smi 실행 실패: {e}")

        # Docker 방법으로 백업 시도 (필요시)
        try:
            logger.info("Docker를 통한 nvidia-smi 실행 시도")
            process = await asyncio.create_subprocess_exec(
                "docker", "run", "--rm", "--gpus=all", 
                "nvidia/cuda:12.1-runtime-ubuntu22.04",
                "nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info("Docker nvidia-smi 실행 성공")
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

                hardware_info = {
                    "gpus": gpus,
                    "gpu_count": len(gpus),
                    "total_vram_gb": sum(gpu["memory_total_mb"] for gpu in gpus) / 1024,
                    "available_vram_gb": sum(gpu["memory_free_mb"] for gpu in gpus) / 1024
                }
                
                # 성공한 결과를 캐시
                self._cached_hardware_info = hardware_info
                return hardware_info
            else:
                logger.warning(f"Docker nvidia-smi 실행 실패: {stderr.decode()}")
        except Exception as e:
            logger.warning(f"Docker 하드웨어 정보 조회 실패: {e}")

        # 캐시된 정보가 있으면 사용
        if self._cached_hardware_info:
            logger.info("nvidia-smi 사용 불가, 캐시된 하드웨어 정보 사용")
            return self._cached_hardware_info

        # 모든 방법 실패시 서비스 실패 처리
        error_msg = "nvidia-smi를 통한 하드웨어 정보 조회에 실패했습니다. 서비스를 사용할 수 없습니다."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    async def _check_vllm_status(self):
        """vLLM 서버 실제 상태 확인"""
        logger.info("vLLM 상태 확인 시작")
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                logger.info("vLLM API 호출 중...")
                response = await client.get("http://vllm-server:8000/v1/models", timeout=3.0)
                logger.info(f"vLLM API 응답: {response.status_code}")
                
                if response.status_code == 200:
                    models_data = response.json()
                    logger.info(f"모델 데이터: {models_data}")
                    
                    if models_data.get("data") and len(models_data["data"]) > 0:
                        # 실행 중인 모델 정보로 현재 프로파일 업데이트
                        model_id = models_data["data"][0]["id"]
                        logger.info(f"실행 중인 모델: {model_id}")
                        
                        for profile_id, profile in self.profiles.items():
                            if profile.model_id == model_id:
                                self.current_profile = profile_id
                                logger.info(f"현재 프로파일 업데이트: {profile_id}")
                                break
                        self.status = "running"
                        logger.info("vLLM 상태: 실행 중")
                        return
        except Exception as e:
            logger.error(f"vLLM 상태 확인 중 오류: {e}")
        
        # API 호출 실패 시 정지 상태로 설정
        self.status = "stopped"
        logger.info("vLLM 상태: 정지됨")

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
