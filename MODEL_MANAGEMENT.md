# 🚀 모델 프로파일 관리 가이드

## 개요

이 시스템은 **RTX 3090** 및 **멀티 GPU 환경**에서 다양한 **HuggingFace 모델**을 효율적으로 사용할 수 있도록 **프로파일 기반 모델 관리**를 제공합니다.

## 🎯 지원 모델

### 🔥 추천 모델 (RTX 3090 최적화)
- **DeepSeek R1 Distill Qwen 14B**: 최신 고성능 모델 (기본값) (`deepseek-r1-distill-qwen-14b`)
- **DeepSeek Coder 7B**: 코딩 작업 특화 (`deepseek-coder-7b`)
- **Qwen2 7B Instruct**: 긴 컨텍스트 지원 (`qwen2-7b-instruct`)
- **Llama 3 8B Instruct**: 최신 Meta 모델 (`llama3-8b-instruct`)
- **Code Llama 7B**: 코딩 전용 모델 (`codellama-7b`)

### 🚀 고성능 모델 (멀티 GPU)
- **DeepSeek R1 Distill Qwen 14B**: 최신 distilled 모델 (2 GPUs) - 기본값
- **DeepSeek Coder 33B**: 고급 코딩 (2+ GPUs)
- **Qwen2 14B Instruct**: 향상된 성능 (32GB+ VRAM)
- **Llama 3 70B Instruct**: 최고 성능 (4+ GPUs)

### 💡 경량 모델 (개발/테스트)
- **Phi-3 Mini 3.8B**: Microsoft 경량 모델

## 🔧 주요 기능

### 1. 자동 하드웨어 호환성 검증
- GPU 수량 및 VRAM 자동 감지
- 모델별 최소/권장 하드웨어 요구사항 확인
- 호환되지 않는 모델 자동 차단

### 2. 하드웨어별 모델 추천
- RTX 3090 단일/듀얼 설정별 최적화
- 현재 하드웨어에 맞는 모델 자동 추천
- 향후 하드웨어 확장 시 추가 모델 제안

## 📋 사용 방법

### 1. 모델 프로파일 설정

`model_profiles.yml` 파일을 편집하여 사용할 모델들을 정의합니다:

```yaml
model_profiles:
  my-custom-model:
    name: "My Custom Model"
    model_id: "huggingface/model-name"
    description: "모델 설명"
    max_model_len: 4096
    tensor_parallel_size: 1
    gpu_memory_utilization: 0.85
    dtype: "float16"
    swap_space: 4

default_profile: "my-custom-model"
```

### 2. 웹 UI에서 모델 선택

1. 웹 브라우저에서 프론트엔드 접속
2. 모델 선택 패널에서 원하는 모델 클릭
3. 모델 전환 시작 (1-3분 소요)
4. 전환 완료 후 새 모델로 대화 시작

### 3. API를 통한 모델 관리

**하드웨어 정보 확인:**
```bash
curl http://localhost:8080/api/models/status
```

**하드웨어 맞춤 추천:**
```bash
curl http://localhost:8080/api/models/hardware-recommendations
```

**모델 전환:**
```bash
curl -X POST http://localhost:8080/api/models/switch \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "deepseek-coder-7b"}'
```

**프로파일 목록 조회:**
```bash
curl http://localhost:8080/api/models/profiles
```

## 🎯 RTX 3090 최적 설정

### 단일 RTX 3090 (24GB)
```yaml
# 권장 설정
gpu_memory_utilization: 0.80  # 안정성 확보
max_model_len: 8192           # 적절한 컨텍스트
tensor_parallel_size: 1       # 단일 GPU
```

### 듀얼 RTX 3090 (48GB)
```yaml
# 33B 모델 설정
gpu_memory_utilization: 0.85
tensor_parallel_size: 2       # 듀얼 GPU
max_model_len: 4096          # 메모리 효율성
```

## 🎯 권장 프로파일

### DeepSeek Coder (코딩)
```yaml
deepseek-coder:
  name: "DeepSeek Coder 7B"
  model_id: "deepseek-ai/deepseek-coder-7b-instruct-v1.5"
  description: "코딩 및 프로그래밍 작업에 특화"
```

### DeepSeek Chat (일반 대화)
```yaml
deepseek-chat:
  name: "DeepSeek Chat 7B"
  model_id: "deepseek-ai/deepseek-llm-7b-chat"
  description: "일반적인 대화 및 질의응답"
```

### Llama 2 Chat
```yaml
llama2-chat:
  name: "Llama 2 7B Chat"
  model_id: "meta-llama/Llama-2-7b-chat-hf"
  description: "Meta의 범용 채팅 모델"
```

## ⚠️ 주의사항

1. **모델 전환 시간**: 대형 모델은 로딩에 시간이 오래 걸립니다
2. **GPU 메모리**: 각 프로파일의 `gpu_memory_utilization` 설정 확인
3. **동시 사용**: 한 번에 하나의 모델만 실행 가능
4. **권한**: Gateway 컨테이너에 Docker 소켓 접근 권한 필요

## 🔧 문제 해결

### 모델 전환 실패
```bash
# Docker 컨테이너 상태 확인
docker compose ps

# vLLM 로그 확인
docker compose logs vllm

# Gateway 로그 확인
docker compose logs gateway
```

### GPU 메모리 부족
- `gpu_memory_utilization` 값을 낮춤 (0.7 ~ 0.8)
- 더 작은 모델로 전환
- `max_model_len` 값 조정

## 📈 모니터링

모델 전환 과정과 상태는 다음을 통해 모니터링할 수 있습니다:

1. **웹 UI**: 실시간 상태 표시
2. **API 엔드포인트**: `/api/models/status`
3. **Docker 로그**: `docker compose logs -f gateway vllm`
4. **GPU 모니터링**: `nvidia-smi`

이제 제한된 GPU 환경에서도 여러 모델을 효율적으로 사용할 수 있습니다! 🎉
