# 👨‍💻 vLLM 서비스 개발자 온보딩 가이드

새로운 팀원이 vLLM 챗봇 서비스 개발에 빠르게 참여할 수 있도록 돕는 단계별 가이드입니다.

## 🎯 온보딩 목표

이 가이드를 완료하면 다음을 할 수 있습니다:
- ✅ 로컬에서 전체 서비스 실행
- ✅ 코드베이스 구조 이해 
- ✅ 모델 관리 시스템 활용
- ✅ 새 기능 개발 및 테스트
- ✅ 배포 프로세스 이해

## 📅 온보딩 일정 (5일 계획)

### **Day 1: 환경 구축 및 시스템 이해**
- [ ] 개발 환경 설정 완료
- [ ] 전체 서비스 로컬 실행 성공
- [ ] 아키텍처 문서 리뷰
- [ ] 첫 번째 API 호출 테스트

### **Day 2: Frontend 개발 환경**
- [ ] React + TypeScript 개발 환경 구축
- [ ] 컴포넌트 구조 이해
- [ ] 모델 관리 UI 사용법 학습
- [ ] 간단한 UI 수정 실습

### **Day 3: Backend (Gateway) 개발**
- [ ] FastAPI 코드 구조 파악
- [ ] 모델 관리 API 심화 학습
- [ ] 데이터베이스 스키마 이해
- [ ] 새로운 API 엔드포인트 추가 실습

### **Day 4: vLLM 및 모델 관리**
- [ ] vLLM 설정 및 최적화 이해
- [ ] model_profiles.yml 설정법 학습
- [ ] 모델 전환 프로세스 실습
- [ ] 성능 모니터링 및 튜닝

### **Day 5: 테스트 및 배포**
- [ ] 단위 테스트 작성법 학습
- [ ] 통합 테스트 실행
- [ ] Docker 배포 프로세스 이해
- [ ] 첫 번째 PR(Pull Request) 제출

---

## 🔧 Day 1: 환경 구축 및 시스템 이해

### **1.1 필수 도구 설치**

#### **시스템 요구사항**
- **OS**: Ubuntu 20.04+ / macOS / Windows WSL2
- **Python**: 3.11+
- **Node.js**: 18+
- **Docker**: 24.0+
- **Git**: 2.30+
- **CUDA**: 12.0+ (GPU 사용 시)

#### **개발 도구 설치**
```bash
# Git 설정
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"

# Python 환경 (pyenv 권장)
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv global 3.11.0

# Node.js 환경 (nvm 권장)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Docker & Docker Compose
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin
sudo usermod -aG docker $USER

# VS Code Extensions 권장
code --install-extension ms-python.python
code --install-extension bradlc.vscode-tailwindcss
code --install-extension esbenp.prettier-vscode
code --install-extension ms-vscode.vscode-typescript-next
```

### **1.2 프로젝트 클론 및 초기 설정**

```bash
# 1. 저장소 클론
git clone https://github.com/seehwan/vllm_seehwan.git
cd vllm_seehwan

# 2. 프로젝트 구조 파악
tree -L 3

# 3. 환경 설정 파일 생성
cp .env.sample .env.local

# 4. 중요한 환경 변수 설정 (실제 값으로 변경 필요)
cat > .env.local << EOF
# Hugging Face 토큰 (필수)
HUGGING_FACE_HUB_TOKEN=hf_your_token_here

# 모델 설정  
MODEL_ID=microsoft/DialoGPT-medium

# GPU 설정
VLLM_UTIL=0.55
VLLM_TP=1

# 데이터베이스
POSTGRES_USER=chatuser
POSTGRES_PASSWORD=secure_password_123
POSTGRES_DB=chatdb
EOF

# 5. Gateway 환경 설정
cd gateway
cat > .env << EOF
JWT_SECRET=dev-jwt-secret-key-for-vllm-gateway-development-only-change-in-production
DEBUG=True
LOG_LEVEL=DEBUG
VLLM_BASE_URL=http://localhost:8000/v1
CORS_ORIGINS=["http://localhost:3000"]
DATABASE_URL=postgresql+asyncpg://chatuser:secure_password_123@localhost:5432/chatdb
REDIS_URL=redis://localhost:6379/0
EOF
cd ..
```

### **1.3 첫 번째 서비스 실행**

```bash
# 1. Docker Compose로 전체 서비스 실행
docker compose up -d

# 2. 서비스 상태 확인
docker compose ps

# 3. 로그 실시간 모니터링 (새 터미널에서)
docker compose logs -f

# 4. 서비스별 헬스체크
echo "🤖 vLLM 상태 확인..."
curl http://localhost:8000/v1/models

echo "🌐 Gateway 상태 확인..."  
curl http://localhost:8080/health

echo "🎨 Frontend 접속 테스트..."
curl http://localhost:3000

echo "📊 데이터베이스 연결 테스트..."
docker compose exec postgres psql -U chatuser -d chatdb -c "SELECT version();"
```

### **1.4 첫 번째 API 호출 테스트**

```bash
# 1. 모델 상태 확인
curl -s http://localhost:8080/api/models/status | jq

# 2. 간단한 채팅 테스트
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "messages": [{"role": "user", "content": "안녕하세요!"}],
    "model": "current",
    "stream": false
  }' | jq

# 3. 모델 프로파일 목록 확인
curl -s http://localhost:8080/api/models/profiles | jq '.profiles | keys'
```

### **1.5 Day 1 완료 체크리스트**

- [ ] 모든 필수 도구 설치 완료
- [ ] 프로젝트 클론 및 환경 설정 완료
- [ ] `docker compose ps`에서 모든 서비스 `Up` 상태
- [ ] Frontend(3000), Gateway(8080), vLLM(8000) 포트 모두 응답
- [ ] 첫 번째 채팅 API 호출 성공
- [ ] 아키텍처 문서(`ARCHITECTURE.md`) 읽기 완료

**🎉 축하합니다! Day 1 완료!**

---

## 🎨 Day 2: Frontend 개발 환경

### **2.1 React + TypeScript 환경 이해**

```bash
cd frontend

# 1. 패키지 설치
npm install

# 2. TypeScript 설정 확인
npx tsc --noEmit

# 3. 개발 서버 실행
npm run dev

# 4. 빌드 테스트
npm run build
```

### **2.2 컴포넌트 구조 탐색**

```bash
# 프론트엔드 구조 파악
tree src -I node_modules

# 주요 파일들 살펴보기
cat src/App.tsx
cat src/components/chat/ChatInterface.tsx
cat src/store/chatStore.ts
```

### **2.3 모델 관리 UI 실습**

**실습 과제: 새로운 모델 상태 표시 컴포넌트 추가**

```typescript
// src/components/chat/ModelBadge.tsx
import React from 'react';
import { Badge } from '../ui/Badge';

interface ModelBadgeProps {
  currentModel: string;
  status: 'running' | 'switching' | 'stopped' | 'error';
}

export const ModelBadge: React.FC<ModelBadgeProps> = ({ currentModel, status }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'switching': return 'bg-yellow-500 animate-pulse';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <Badge className={`${getStatusColor(status)} text-white`}>
      🤖 {currentModel} ({status})
    </Badge>
  );
};
```

### **2.4 Day 2 실습 과제**

1. **컴포넌트 생성**: 위의 `ModelBadge` 컴포넌트 구현
2. **상태 관리**: Zustand store에서 모델 상태 관리 추가
3. **API 연동**: 모델 상태 API 호출 로직 구현
4. **UI 통합**: 메인 채팅 화면에 모델 배지 표시

---

## 🔧 Day 3: Backend (Gateway) 개발

### **3.1 FastAPI 코드 구조 이해**

```bash
cd gateway

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 코드 구조 탐색
tree app -I __pycache__

# 중요한 파일들 살펴보기
cat app/main.py
cat app/routers/models.py
cat app/services/model_manager.py
```

### **3.2 모델 관리 API 심화**

**실습: 새로운 API 엔드포인트 추가**

```python
# app/routers/models.py에 추가
@router.get("/models/statistics")
async def get_model_statistics():
    """모델 사용 통계 조회"""
    try:
        # 간단한 통계 정보 반환
        return {
            "current_model": model_manager.current_profile,
            "total_switches": getattr(model_manager, 'switch_count', 0),
            "uptime_seconds": time.time() - getattr(model_manager, 'start_time', time.time()),
            "gpu_usage": await model_manager._get_hardware_info()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **3.3 데이터베이스 연동 이해**

```bash
# 데이터베이스 스키마 확인
docker compose exec postgres psql -U chatuser -d chatdb -c "\dt"

# 마이그레이션 실행
alembic upgrade head

# 새 마이그레이션 생성 (예시)
alembic revision --autogenerate -m "Add model usage tracking"
```

---

## 🤖 Day 4: vLLM 및 모델 관리

### **4.1 model_profiles.yml 이해 및 수정**

```yaml
# 새 모델 프로파일 추가 실습
custom-test-model:
  name: "Custom Test Model"
  model_id: "microsoft/DialoGPT-small"  # 작은 모델로 테스트
  description: "개발자 온보딩용 테스트 모델"
  max_model_len: 2048
  tensor_parallel_size: 1
  gpu_memory_utilization: 0.5
  dtype: "float16"
  swap_space: 2
  hardware_requirements:
    min_vram_gb: 4
    recommended_vram_gb: 8
```

### **4.2 모델 전환 실습**

```bash
# 1. 현재 모델 상태 확인
curl http://localhost:8080/api/models/status | jq

# 2. 사용 가능한 모델 목록 확인  
curl http://localhost:8080/api/models/profiles | jq '.profiles | keys'

# 3. 작은 모델로 전환 (빠른 테스트용)
curl -X POST http://localhost:8080/api/models/switch \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "phi3-mini"}'

# 4. 전환 완료까지 상태 모니터링
watch -n 2 'curl -s http://localhost:8080/api/models/status | jq .status'
```

---

## 🧪 Day 5: 테스트 및 배포

### **5.1 테스트 작성 실습**

```python
# tests/test_model_management.py
import pytest
from fastapi.testclient import TestClient
from gateway.app.main import app

client = TestClient(app)

def test_get_model_status():
    response = client.get("/api/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "current_profile" in data
    assert "status" in data

def test_get_model_profiles():
    response = client.get("/api/models/profiles")
    assert response.status_code == 200
    data = response.json()
    assert "profiles" in data
    assert len(data["profiles"]) > 0

def test_model_switch_invalid_profile():
    response = client.post(
        "/api/models/switch",
        json={"profile_id": "non-existent-model"}
    )
    assert response.status_code == 404
```

### **5.2 성능 테스트 실행**

```bash
cd k6

# 부하 테스트 실행
k6 run load-test.js

# 스트리밍 테스트
k6 run streaming-test.js

# 결과 분석
echo "테스트 결과를 분석하고 성능 병목점을 찾아보세요"
```

### **5.3 첫 번째 기여하기**

**실습 과제: 개발자 본인만의 작은 개선사항 구현**

예시 아이디어:
1. 새로운 API 엔드포인트 추가
2. Frontend UI 개선
3. 에러 처리 강화
4. 문서 개선
5. 테스트 커버리지 향상

---

## 📚 추가 학습 리소스

### **문서 읽기 순서**
1. `README.md` - 전체 프로젝트 개요
2. `ARCHITECTURE.md` - 시스템 아키텍처  
3. `GETTING_STARTED.md` - 빠른 시작 가이드
4. `gateway/GATEWAY_GUIDE.md` - Gateway API 상세
5. `MODEL_MANAGEMENT.md` - 모델 관리 심화
6. `OPERATIONS.md` - 운영 가이드

### **유용한 명령어 모음**

```bash
# 개발 환경 명령어 모음
alias vllm-status="curl -s http://localhost:8080/api/models/status | jq"
alias vllm-profiles="curl -s http://localhost:8080/api/models/profiles | jq '.profiles | keys'"
alias vllm-logs="docker compose logs -f gateway vllm"
alias vllm-restart="docker compose restart gateway vllm"

# ~/.bashrc 또는 ~/.zshrc에 추가
```

### **문제 해결**

**자주 발생하는 문제들:**

1. **Docker 권한 오류**
   ```bash
   sudo usermod -aG docker $USER
   # 로그아웃 후 재로그인 필요
   ```

2. **포트 충돌**
   ```bash
   sudo lsof -i :3000  # 포트 사용 중인 프로세스 확인
   kill -9 <PID>       # 해당 프로세스 종료
   ```

3. **CUDA/GPU 문제**
   ```bash
   nvidia-smi          # GPU 상태 확인
   docker compose logs vllm | grep -i cuda  # CUDA 오류 확인
   ```

---

## ✅ 온보딩 완료 체크리스트

### **기술 역량**
- [ ] 로컬 개발 환경에서 모든 서비스 실행 가능
- [ ] React + TypeScript로 새 컴포넌트 개발 가능
- [ ] FastAPI로 새 API 엔드포인트 추가 가능
- [ ] 모델 전환 프로세스 이해 및 실행 가능
- [ ] 기본적인 테스트 작성 및 실행 가능

### **프로세스 이해**
- [ ] Git workflow 이해 (branch, commit, PR)
- [ ] 코드 리뷰 프로세스 이해
- [ ] 배포 프로세스 이해
- [ ] 문서 업데이트 프로세스 이해

### **첫 번째 기여**
- [ ] 첫 번째 Pull Request 제출 완료
- [ ] 코드 리뷰 수신 및 반영 경험
- [ ] 머지 완료 및 배포 확인

**🎊 축하합니다! vLLM 서비스 개발팀의 정식 멤버가 되었습니다!**

---

## 📞 도움이 필요할 때

- **기술 질문**: 팀 Slack #dev-questions 채널
- **온보딩 관련**: 멘토 또는 Tech Lead에게 직접 문의
- **문서 개선**: 이 가이드의 부족한 부분을 발견하면 PR로 개선해주세요!

**Happy Coding! 🚀**
