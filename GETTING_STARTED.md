# 🎯 vLLM 챗봇 서비스 시작 가이드

이 문서는 vLLM 기반 챗봇 서비스를 처음 시작하는 개발자를 위한 단계별 가이드입니다.

## 📋 체크리스트

### ✅ 시작 전 확인사항

- [ ] **시스템 요구사항 충족**

  - [ ] Ubuntu 22.04 LTS
  - [ ] NVIDIA GPU (RTX 3090 x2 권장)
  - [ ] NVIDIA Driver 535+
  - [ ] Docker 24.x+ & Docker Compose v2
  - [ ] 16GB+ RAM, 100GB+ 디스크 여유 공간

- [ ] **필수 계정 및 토큰**

  - [ ] Hugging Face 계정 및 토큰 발급
  - [ ] GitHub 계정 (선택사항)

- [ ] **개발 도구 설치**
  - [ ] Git, curl, wget
  - [ ] 코드 에디터 (VS Code 권장)

## 🚀 1단계: 환경 설정

### 1.1 시스템 요구사항 검증

```bash
# GPU 상태 확인
nvidia-smi

# Docker 설치 확인
docker --version
docker compose version

# 디스크 용량 확인
df -h

# 메모리 확인
free -h
```

### 1.2 프로젝트 클론 및 초기 설정

```bash
# 프로젝트 클론 (Git 사용시)
git clone https://github.com/your-username/vllm_seehwan.git
cd vllm_seehwan

# 또는 ZIP 다운로드 후 압축 해제
# unzip vllm_seehwan.zip && cd vllm_seehwan

# 실행 권한 부여
chmod +x scripts/*.sh

# 환경변수 파일 생성
cp .env.sample .env.local
```

### 1.3 환경변수 설정 (.env.local)

```bash
# 필수 편집 항목
nano .env.local
```

**⚠️ 반드시 수정해야 할 항목들:**

```bash
# Hugging Face 토큰 (필수)
HUGGING_FACE_HUB_TOKEN=hf_your_token_here

# JWT 보안 키 (필수 - 복잡한 랜덤 문자열로 변경)
JWT_SECRET=your-super-secret-jwt-key-minimum-32-characters

# 데이터베이스 비밀번호 (보안을 위해 변경)
POSTGRES_PASSWORD=your_secure_password_here

# vLLM 모델 설정 (필요에 따라 조정)
MODEL_ID=microsoft/DialoGPT-medium

# GPU 메모리 사용률 (OOM 발생시 0.3~0.4로 낮춤)
VLLM_UTIL=0.55
```

**💡 Hugging Face 토큰 발급 방법:**

1. https://huggingface.co 계정 생성
2. Settings → Access Tokens
3. "New token" 생성 (Read 권한)
4. 토큰을 .env.local에 복사

## 🎯 2단계: 자동 설치 실행

### 2.1 원클릭 설치

```bash
# 전체 서비스 자동 설치
./scripts/setup.sh
```

**설치 과정에서 수행되는 작업:**

- [ ] 시스템 요구사항 검증
- [ ] NVIDIA Container Toolkit 설치/확인
- [ ] Docker 이미지 빌드
- [ ] 데이터베이스 초기화
- [ ] 서비스 시작 및 헬스체크

### 2.2 설치 완료 확인

성공적으로 완료되면 다음 메시지가 표시됩니다:

```
✅ vLLM 서비스 설치 완료!

서비스 접속 정보:
  - Frontend: http://localhost:3000
  - API Gateway: http://localhost:8080
  - API 문서: http://localhost:8080/docs
  - vLLM API: http://localhost:8000
  - 데이터베이스 관리: http://localhost:8081 (Adminer)
```

## 🔍 3단계: 서비스 확인 및 테스트

### 3.1 기본 동작 테스트

```bash
# 1. 헬스체크
curl http://localhost:8080/health

# 2. vLLM 모델 확인
curl http://localhost:8000/v1/models

# 3. Frontend 접속
# 브라우저에서 http://localhost:3000 열기

# 4. API 문서 확인
# 브라우저에서 http://localhost:8080/docs 열기
```

### 3.2 간단한 채팅 테스트

```bash
# API를 통한 채팅 테스트
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "model": "microsoft/DialoGPT-medium"
  }'
```

### 3.3 서비스 상태 모니터링

```bash
# 전체 서비스 상태 확인
docker compose ps

# 실시간 로그 모니터링
docker compose logs -f

# GPU 사용률 확인
nvidia-smi

# 특정 서비스 로그만 확인
docker compose logs -f vllm
docker compose logs -f gateway
docker compose logs -f frontend
```

## 📊 4단계: 성능 테스트

### 4.1 벤치마크 실행

```bash
# 종합 성능 테스트 (5-10분 소요)
./scripts/benchmark.sh
```

### 4.2 결과 분석

벤치마크 완료 후 생성되는 파일들:

```bash
# 결과 디렉토리 확인
ls -la benchmark_results_*/

# 요약 보고서 확인
cat benchmark_results_*/benchmark_summary.md

# 주요 성능 지표 확인
cat benchmark_results_*/load_test_summary.txt | grep -A 10 'checks'
```

**목표 성능 기준:**

- ✅ TTFT (첫 토큰까지 시간) < 2초
- ✅ 처리량 > 20 RPS
- ✅ 에러율 < 1%
- ✅ GPU 사용률 50-80%

## 🛠 5단계: 개발 환경 설정 (선택사항)

### 5.1 개발 모드 실행

```bash
# 핫리로딩 지원 개발 모드
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 또는 개별 서비스만 개발 모드로
docker compose -f docker-compose.yml -f docker-compose.dev.yml up frontend gateway -d
```

### 5.2 로컬 개발 환경 (선택사항)

#### Frontend 로컬 개발

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000에서 개발
```

#### Gateway 로컬 개발

```bash
cd gateway
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

## 🎨 6단계: 커스터마이징

### 6.1 모델 변경

**.env.local에서 모델 설정:**

```bash
# 더 작은 모델 (메모리 절약)
MODEL_ID=microsoft/DialoGPT-small

# 더 큰 모델 (성능 향상, 메모리 더 필요)
MODEL_ID=microsoft/DialoGPT-large

# 다른 모델 (Hugging Face에서 지원하는 모델)
MODEL_ID=facebook/blenderbot-400M-distill
```

### 6.2 성능 튜닝

**GPU 메모리 부족 시:**

```bash
# vLLM 설정 조정
VLLM_TP=1              # Tensor Parallel 감소
VLLM_MAXLEN=2048       # 최대 시퀀스 길이 감소
VLLM_UTIL=0.3          # GPU 메모리 사용률 감소
VLLM_SWAP_SPACE=4      # 스왑 공간 감소
```

**성능 향상을 위한 설정:**

```bash
# 더 많은 GPU 메모리 활용
VLLM_UTIL=0.8
VLLM_MAXLEN=8192

# 더 많은 병렬 처리
VLLM_TP=2              # GPU가 2개 이상일 때
```

### 6.3 UI/UX 커스터마이징

**Frontend 테마 변경:**

```bash
# frontend/tailwind.config.js 편집
nano frontend/tailwind.config.js

# 색상, 폰트, 레이아웃 등 수정 가능
```

## 🔒 7단계: 보안 및 프로덕션 준비

### 7.1 보안 설정 강화

```bash
# 강력한 JWT 시크릿 생성
openssl rand -base64 32

# 데이터베이스 비밀번호 변경
# PostgreSQL 접속 후 비밀번호 변경
```

### 7.2 SSL/HTTPS 설정 (프로덕션용)

```bash
# Let's Encrypt 인증서 발급 (도메인 필요)
sudo certbot --nginx -d yourdomain.com

# 또는 자체 서명 인증서 생성 (개발용)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

### 7.3 방화벽 설정

```bash
# UFW 방화벽 설정 (Ubuntu)
sudo ufw allow 22          # SSH
sudo ufw allow 80          # HTTP
sudo ufw allow 443         # HTTPS
sudo ufw --force enable
```

## 🚨 트러블슈팅 가이드

### 자주 발생하는 문제와 해결방법

#### 1. GPU 메모리 부족 (OOM) 에러

**증상:**

```
RuntimeError: CUDA out of memory
```

**해결방법:**

```bash
# .env.local에서 다음 값들 조정
VLLM_UTIL=0.3        # 0.55에서 0.3으로 감소
VLLM_MAXLEN=2048     # 8192에서 2048로 감소
VLLM_TP=1           # 2에서 1로 감소 (GPU 1개만 사용)
```

#### 2. 모델 다운로드 실패

**증상:**

```
HTTP 403: Forbidden (Hugging Face)
```

**해결방법:**

```bash
# Hugging Face 토큰 확인 및 재설정
echo $HUGGING_FACE_HUB_TOKEN
# 토큰이 올바른지 확인하고 .env.local 재편집
```

#### 3. 서비스 시작 실패

**증상:**

```
docker compose up 실패
```

**해결방법:**

```bash
# 로그 확인
docker compose logs

# 포트 충돌 확인
netstat -tlnp | grep -E "(3000|8000|8080)"

# 기존 컨테이너 정리
docker compose down
docker system prune -f
```

#### 4. 느린 응답 속도

**해결방법:**

```bash
# GPU 사용률 확인
nvidia-smi

# vLLM 로그 확인
docker compose logs vllm | grep -i "error\|warning"

# 벤치마크로 성능 측정
./scripts/benchmark.sh
```

## 📚 8단계: 심화 학습 리소스

### 8.1 각 모듈별 상세 문서

1. **Frontend 개발**: `frontend/README.md`

   - React 컴포넌트 구조
   - 상태 관리 (Zustand)
   - UI/UX 커스터마이징

2. **Gateway API**: `gateway/README.md`

   - FastAPI 아키텍처
   - 인증 시스템
   - 데이터베이스 스키마

3. **운영 스크립트**: `scripts/README.md`

   - 자동화 도구 사용법
   - 데이터베이스 관리
   - 백업 및 복구

4. **성능 테스트**: `k6/README.md`

   - 부하 테스트 시나리오
   - 메트릭 분석 방법
   - 성능 최적화 전략

5. **Nginx 설정**: `nginx/README.md`
   - 리버스 프록시 구성
   - SSL/TLS 설정
   - 로드 밸런싱

### 8.2 추가 개발 가이드

#### API 엔드포인트 추가

```bash
# 1. gateway/app/schemas/ 에서 스키마 정의
# 2. gateway/app/routers/ 에서 라우터 구현
# 3. gateway/app/services/ 에서 비즈니스 로직 작성
# 4. tests/ 에서 테스트 코드 추가
```

#### 새로운 모델 통합

```bash
# 1. Hugging Face에서 모델 호환성 확인
# 2. .env.local에서 MODEL_ID 변경
# 3. vLLM 재시작 후 테스트
# 4. 성능 벤치마크 재실행
```

#### UI 컴포넌트 확장

```bash
# 1. frontend/src/components/ 에서 컴포넌트 작성
# 2. Tailwind CSS로 스타일링
# 3. Zustand 스토어와 상태 연동
# 4. 테스트 코드 작성
```

## 🎯 9단계: 다음 단계 로드맵

### 단기 목표 (1-2주)

- [ ] **기본 기능 완성**

  - [ ] 안정적인 채팅 서비스 구현
  - [ ] 사용자 인증 시스템 적용
  - [ ] 대화 저장/불러오기 기능

- [ ] **성능 최적화**
  - [ ] 목표 성능 기준 달성
  - [ ] GPU 리소스 최적 활용
  - [ ] 응답 시간 개선

### 중기 목표 (1-2개월)

- [ ] **기능 확장**

  - [ ] 다중 모델 지원
  - [ ] 파일 업로드/분석 기능
  - [ ] 시스템 프롬프트 커스터마이징

- [ ] **운영 안정화**
  - [ ] 모니터링 대시보드 구축
  - [ ] 자동 백업 시스템
  - [ ] 로그 분석 도구

### 장기 목표 (3-6개월)

- [ ] **고급 기능**

  - [ ] RAG (검색 증강 생성) 구현
  - [ ] 다국어 지원
  - [ ] 음성 인터페이스 추가

- [ ] **확장성**
  - [ ] Kubernetes 배포
  - [ ] 마이크로서비스 분해
  - [ ] 다중 GPU 클러스터 지원

## 📞 지원 및 커뮤니티

### 문제 해결 순서

1. **로그 확인**: `docker compose logs [service]`
2. **문서 검색**: 각 모듈별 README.md 참고
3. **이슈 검색**: GitHub Issues 확인
4. **커뮤니티 질문**: 개발자 커뮤니티 문의

### 유용한 링크

- **vLLM 공식 문서**: https://vllm.readthedocs.io/
- **FastAPI 문서**: https://fastapi.tiangolo.com/
- **React 문서**: https://react.dev/
- **Docker 문서**: https://docs.docker.com/

---

## ✅ 완료 체크리스트

프로젝트 설정이 완료되었다면 아래 항목들을 확인해보세요:

- [ ] 모든 서비스가 정상 실행 중 (`docker compose ps`)
- [ ] Frontend에서 채팅 가능 (http://localhost:3000)
- [ ] API 문서 접속 가능 (http://localhost:8080/docs)
- [ ] vLLM 모델 로딩 완료 (`curl http://localhost:8000/v1/models`)
- [ ] 성능 테스트 통과 (`./scripts/benchmark.sh`)
- [ ] 개발 환경 설정 완료 (필요시)

축하합니다! 🎉 이제 vLLM 기반 챗봇 서비스가 완전히 준비되었습니다.

**다음 단계:** 각 모듈별 README를 참고하여 프로젝트를 원하는 방향으로 커스터마이징해보세요!
