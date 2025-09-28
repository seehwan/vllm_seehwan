# SW 서비스 개발기획서 — vLLM 기반 챗봇 (MVP→운영)

> 본 문서는 vLLM(OpenAI 호환) + FastAPI 게이트웨이 + React 프론트엔드 기반의 스트리밍 챗봇 서비스를 **기획·설계·구현·운영**하기 위한 표준 형식으로 재정리되었습니다.

## 🚀 빠른 시작

```bash
# 시스템 시작
./start

# 상태 확인
./status

# 로그 확인
./logs

# 도움말
./help
```

## 🎯 현재 구현 상태 (2024)

### ✅ 완료된 기능
- **JWT 인증 시스템**: 토큰 기반 인증, BCrypt 비밀번호 해싱, HTTPBearer 보안
- **하드웨어 모니터링**: Docker 컨테이너에서 nvidia-smi 실행, GPU 정보 수집
- **서비스 연결성**: Gateway-vLLM-Database 간 연결 확인
- **API 엔드포인트**: 인증, 채팅, 모델 관리, 헬스체크 API 구현
- **개발 모드**: 인증 우회 기능으로 개발 편의성 제공

### 🔧 기술 스택 검증
- **FastAPI**: JWT 토큰 발급/검증, SSE 스트리밍, 보안 미들웨어
- **Docker**: NVIDIA 장치 마운팅, 컨테이너 간 통신
- **React**: 프론트엔드 UI, API 연동 준비
- **PostgreSQL/Redis**: 데이터베이스 연결 확인

### 📊 테스트 결과 (최신 검증)
- **헬스체크**: `GET /health` → `{"status":"healthy","service":"vLLM Chat Gateway","version":"1.0.0"}`
- **JWT 로그인**: `POST /api/auth/login` → 올바른 엔드포인트 확인, 토큰 발급 성공
- **실제 채팅**: vLLM API 직접 호출 및 Gateway 통한 채팅 완성 응답 확인
- **GPU 사용률**: RTX 3090 × 2 (각각 87% 사용률, 모델 정상 로딩)
- **API 수정사항**: 
  - 인증 엔드포인트: `/auth/token` → `/api/auth/login`
  - 테스트 계정: `admin/secret` → `admin/admin123`

---

## 문서 정보

- **버전**: v1.3 (API 검증 및 수정사항 반영)
- **작성일**: 2025-08-17 (Asia/Seoul)
- **소유/검토**: PM · Tech Lead · MLOps · Frontend Lead · Backend Lead
- **적용 범위**: 개발(MVP) → 운영(단일 노드) → 확장(멀티 노드)

### 용어/약어

- **vLLM**: 고성능 LLM 서버(OpenAI 호환 API)
- **TTFT**: Time To First Token
- **TP**: Tensor Parallelism
- **SSE**: Server-Sent Events(스트리밍)
- **KPI/SLA**: 핵심 성과지표/서비스 수준

---

## 1) 배경 · 목표 · 비전

- **배경**: 내부/외부 사용자 대상 질의응답·도우미용 LLM 챗봇 니즈 증가. 로컬 GPU(2× RTX 3090) 자원 활용.
- **목표**: vLLM 기반 **스트리밍 대화** 경험 제공, 운영 가능한 **API/프론트** 구성, **데이터·관측·보안**을 갖춘 MVP.
- **비전**: 모델/프롬프트/플러그인(툴콜) 레이어를 모듈화해 도메인별 챗봇을 신속히 파생.

---

## 2) 서비스 범위(스코프)

### 2.1 In-Scope (MVP)

- 스트리밍 채팅(SSE), 시스템 프롬프트, **동적 모델 전환(프로파일 기반)**, 대화 저장/불러오기
- 인증(토큰), 사용량 로깅, 기본 레이트리밋, 기본 모니터링/로그 수집
- **모델 관리 UI**: 웹에서 모델 선택 및 전환, 실시간 상태 모니터링

### 2.2 Out-of-Scope (MVP)

- RAG/검색증강, 파일 업로드 요약, 고급 툴콜(코드실행/브라우징), 결제/구독, 조직 테넌시
- 다중 리전/DR, 멀티 노드 오토스케일링(차기 단계)

### 2.3 이해관계자/페르소나

- **엔드유저**: 질의응답/도우미 사용, 반응성·정확성
- **운영자**: 모델/프롬프트 정책, 사용량/오류 모니터링
- **개발자**: API 통합, 실험·A/B, 로그 기반 개선

---

## 3) 성공지표(KPI)

- **TTFT(p50)** < 1.5s @ ctx 2k
- **처리량** ≥ 30 req/min (동시 5 세션 기준, 모델·파라미터에 따라 조정)
- **오류율** < 1% (5xx 기준)
- **가용성** > 99.5% (단일 노드)

> 벤치 결과에 따라 p95/p99 목표 재설정.

---

## 4) 요구사항

### 4.1 기능 요구사항 (요약)

- FR-1: 사용자 메시지 송신 시 **SSE 스트리밍**으로 토큰 수신
- FR-2: **시스템 프롬프트** 지정/저장(사용자별 기본값)
- FR-3: **모델 선택**(화이트리스트·별칭) 및 기본 파라미터(temperature 등)
- FR-4: **대화 저장/불러오기**(최근 N개) 및 제목 자동화(요약)
- FR-5: **토큰 인증**(Bearer) 및 사용자/권한(관리자)
- FR-6: **사용량 로깅**(토큰/지연/상태), 다운로드(CSV)
- FR-7: **오류 처리**(타임아웃/취소/서버오류 표준 응답)

### 4.2 비기능 요구사항 (요약)

- NFR-성능: KPI 충족(§3), 동시 n=5 이상에서 안정적인 스트리밍
- NFR-신뢰성: 프로세스 재시작 정책, 헬스체크, 데이터 영속성
- NFR-보안: TLS, 인증, 입력 검증/마스킹, CORS 화이트리스트
- NFR-관측: 구조화 로그/메트릭/트레이싱, 샘플링 보관(PII 마스킹)
- NFR-확장성: 모델·컨텍스트·동시성 분리/튜닝, 수평 확장 가능 설계

### 4.3 제약/가정

- 하드웨어: **RTX 3090 × 2 (24GB)**, Ubuntu 22.04
- 모델: HF Hub 제공(필요 시 토큰), vLLM로 서빙
- 운영: 단일 노드 compose 우선, 이후 k8s 확장 검토

---

## 5) 아키텍처 (MVP→확장)

### 5.1 전체 구성

- **Frontend(React/Vite)** ↔ **Gateway(FastAPI)** ↔ **vLLM(OpenAI 호환)** ↔ **HF 모델 저장소**
- (옵션) **Postgres**(대화/사용량), **Redis**(레이트리밋), **Nginx/Traefik**(TLS/리버스프록시)

### 5.2 컴포넌트 책임

- **Frontend**: SSE 채팅 UI, 시스템 프롬프트·모델 선택, 복사/초기화
- **Gateway**: 인증, 레이트리밋, 요청 검증/스키마, CORS, 로깅/메트릭, **🎯 통합 모델 관리**, **템플릿 일관화**(chat_template 부재 시 적용), **취소/타임아웃 전파**
  - **모델 관리 서비스**: 프로파일 기반 동적 전환, 하드웨어 호환성 검증, RTX 3090 최적화, 10개 모델 지원
- **vLLM**: 모델 로딩/서빙, TP·KV 캐시·배치 스케줄링

### 5.3 데이터 흐름

브라우저 → Gateway(검증/인증·로깅) → vLLM(`/v1/chat/completions`) → Gateway(후처리) → 브라우저(SSE)

### 5.4 운영 권고

- **SSE 안정화**: 프록시 버퍼링 off, read_timeout 상향, HTTP/1.1
- **GPU 운용**: GPU0가 데스크탑 점유 시 vLLM은 GPU1 고정, OOM 시 `--gpu-memory-utilization`↓·`--max-model-len`↓·`--swap-space` 활용
- **확장 경로**: 인스턴스 수평 확장(+L7 라우팅), 대용량 컨텍스트 전용 인스턴스 분리, k8s에서 GPU 핀닝

---

## 6) 기술 스택 · 필요한 모듈

### 6.1 프론트엔드 (React/Vite)

- **필수**: `react`, `react-dom`, `vite`, `typescript`; 스타일: `tailwindcss`, `postcss`, `autoprefixer`
- **권장**: `react-markdown`, `remark-gfm`, `zustand`, `lucide-react`, `class-variance-authority`, `tailwind-merge`
- **테스트/품질**: `vitest`, `@testing-library/*`, `eslint`, `prettier`

### 6.2 게이트웨이(FastAPI)

- **핵심**: `fastapi`, `uvicorn[standard]`, `httpx`, `pydantic`, `pydantic-settings`
- **보안**: `python-jose[cryptography]`/`pyjwt`, `passlib[bcrypt]`
- **레이트리밋/캐시**: `slowapi`/`limits`, `redis`
- **DB/마이그레이션**: `SQLAlchemy(2.x)`, `asyncpg`/`psycopg[binary]`, `alembic`
- **관측/품질**: `prometheus-client`, `structlog`/`loguru`, `pytest`, `pytest-asyncio`, `ruff`, `black`, `mypy`

### 6.3 vLLM/모델

- 이미지: `vllm/vllm-openai:latest` (운영은 태그 고정)
- 모델: HF Hub(필요 시 `HUGGING_FACE_HUB_TOKEN`), **`--chat-template`**(필요시)

### 6.4 DevOps/운영 도구

- 리버스 프록시: **Nginx**(TLS, SSE 버퍼링 해제)
- 부하/관측: **k6**, **vegeta**, **Grafana/Loki/Prometheus**(후속)
- 공통: **docker**, **docker compose**, **pre-commit**

---

## 7) 개발환경(로컬/개발/운영)

### 7.1 호스트 요건

- Ubuntu 22.04, **RTX 3090 × 2**, NVIDIA 드라이버 **535+**, Docker **24.x+**, Compose v2, NVIDIA Container Toolkit

### 7.2 초기 점검

```bash
nvidia-smi
sudo apt-get install -y nvidia-container-toolkit && sudo systemctl restart docker
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

### 7.2.1 Gateway 컨테이너 NVIDIA 통합

Gateway 컨테이너에서 `nvidia-smi` 실행을 위한 필수 설정:

```yaml
# docker-compose.yml의 gateway 서비스
gateway:
  devices:
    - "/dev/nvidia0:/dev/nvidia0"
    - "/dev/nvidia1:/dev/nvidia1"
    - "/dev/nvidiactl:/dev/nvidiactl"
    - "/dev/nvidia-uvm:/dev/nvidia-uvm"
  volumes:
    - "/usr/bin/nvidia-smi:/usr/bin/nvidia-smi:ro"
    - "/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1:/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1:ro"
```

**목적**: Gateway의 모델 관리 서비스에서 GPU 하드웨어 정보 실시간 모니터링

### 7.3 리포 구조(예시)

```
repo-root/
 ├─ docker-compose.yml
 ├─ docker-compose.dev.yml
 ├─ .env.sample
 ├─ frontend/
 ├─ gateway/
 └─ scripts/
```

### 7.4 환경변수(.env.sample)

```dotenv
MODEL_ID=deepseek-ai/DeepSeek-R1-Distill-Qwen-14B
HUGGING_FACE_HUB_TOKEN=
VLLM_TP=2
VLLM_MAXLEN=8192
VLLM_UTIL=0.55
FRONTEND_PORT=3000
GATEWAY_PORT=8080
VLLM_PORT=8000
CORS_ORIGINS=http://localhost:3000
JWT_SECRET=change-me
POSTGRES_HOST=postgres
POSTGRES_DB=chat
POSTGRES_USER=app
POSTGRES_PASSWORD=pass
REDIS_URL=redis://redis:6379
```

### 7.5 개발용 compose 오버레이(핫리로드)

```yaml
override example:
version: '3.9'
services:
  frontend:
    volumes:
      - ./frontend:/app
    command: sh -c "npm ci && npm run dev -- --host 0.0.0.0"
  gateway:
    volumes:
      - ./gateway:/app
    command: sh -c "pip install -r requirements.txt && uvicorn app.main:app --reload --host 0.0.0.0 --port 8080"
```

### 7.6 로컬 TLS & CORS

- CORS 허용 도메인에 프론트엔드 도메인 추가, 개발용 TLS는 `mkcert` 사용

### 7.7 자주 겪는 이슈

- **vLLM 서비스 불안정**: 간헐적 Exit 1 상태, NCCL 통신 오류로 인한 재시작 발생 가능
- OOM/부팅 실패: `VLLM_UTIL`↓, `VLLM_MAXLEN`↓, `--swap-space 8`
- GPU0 점유: vLLM을 GPU1로 고정
- 모델 404/권한: 모델 ID 확인·HF 토큰 사용

> **개발환경 vs 필요한 모듈**: 환경=런타임 전제조건(OS/GPU/Docker), 모듈=앱 패키지(프론트/게이트웨이/DB/DevOps).

---

## 8) 데이터 설계

```sql
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  role TEXT DEFAULT 'user',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE conversations (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  title TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE messages (
  id BIGSERIAL PRIMARY KEY,
  conv_id BIGINT REFERENCES conversations(id),
  role TEXT CHECK (role IN ('system','user','assistant')),
  content TEXT NOT NULL,
  token_in INT,
  token_out INT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE requests (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  model TEXT,
  latency_ms INT,
  input_tokens INT,
  output_tokens INT,
  status_code INT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 9) API 설계 및 인증

### 9.1 JWT 인증 시스템

#### 인증 엔드포인트
- `POST /api/auth/login` — 로그인 및 토큰 발급
  - 바디: `{ "username": "string", "password": "string" }`
  - 응답: `{ "access_token": "jwt_token", "token_type": "bearer" }`
  - 토큰 유효기간: 30분
  
- `GET /api/auth/verify` — 토큰 검증 (개발용)
  - 헤더: `Authorization: Bearer <token>`
  - 응답: `{ "username": "string", "exp": timestamp }`

#### 테스트 계정
- 사용자명: `admin`, 비밀번호: `admin123`
- 추가 계정: `test` / `test`
- JWT 알고리즘: HS256
- 비밀번호 해시: BCrypt

#### 개발 모드
- 환경변수 `DEVELOPMENT_MODE=true` 설정 시 인증 우회 가능
- 프로덕션 환경에서는 반드시 `false` 또는 미설정

### 9.2 주요 API 엔드포인트

#### 채팅 API
- `POST /api/chat` — 채팅 완성 (SSE 스트리밍)
  - 헤더: `Authorization: Bearer <token>`
  - 바디: `{ "messages": [], "model": "string", "temperature": number, "max_tokens": number }`
  - 응답: vLLM `/v1/chat/completions` 프록시 (Server-Sent Events)

#### 모델 관리 API
- `GET /api/models` — 사용 가능한 모델 목록
  - 헤더: `Authorization: Bearer <token>`
  - 응답: `{ "models": [{ "id": "string", "name": "string" }] }`

#### 대화 관리 API
- `GET /api/conversations/:id` — 대화 로드
- `POST /api/conversations` — 새 대화 생성
- 헤더: `Authorization: Bearer <token>`

#### 헬스 체크
- `GET /health` — 서비스 상태 확인 (인증 불필요)
  - 응답: `{ status: "ok", services: { ... } }`

### 9.3 서비스 연결 상태 (검증완료)

```bash
# Gateway API 상태 확인
curl http://localhost:8080/health
# → {"status":"healthy","service":"vLLM Chat Gateway","version":"1.0.0"}

# 1. 토큰 발급 테스트 (올바른 엔드포인트와 비밀번호)
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# → {"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","token_type":"bearer"}

# 2. 인증된 채팅 API 호출
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
    "messages": [{"role": "user", "content": "안녕하세요!"}],
    "max_tokens": 50
  }'
# → SSE 스트림 응답

# 3. 모델 목록 조회
curl http://localhost:8080/api/models \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
# → {"models":[{"id":"deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",...}]}

# 4. vLLM 서버 직접 테스트 (인증 불필요)
curl http://localhost:8000/version
# → {"version":"0.5.0"}
```

---

## 10) 관측/로깅

- 로그 항목: `request_id`, `user_id`, `model`, `ctx_len`, `input_tokens`, `output_tokens`, `latency_ms`, `status_code`
- 메트릭: 요청 수/지연(p50/p95)/에러율, 모델별 토큰 사용량
- 대시보드: 초기 DB/CSV → Grafana/Loki/Prometheus 확장

---

## 11) 성능 전략 & 용량 산정

- vLLM 시작값(2×3090): `TP=2`, `dtype=fp16`, `max-len=8192`, `util=0.55`, `(옵션) swap=8`
- 튜닝 순서: TTFT/TPOT 측정 → `util↑`, `max-num-seqs↑` → OOM 시 컨텍스트↓·swap↑
- 모델 선택: 14B FP16 → 필요 시 8B/양자화(AWQ/GPTQ)

---

## 12) 보안 및 인증 구현

### 12.1 JWT 기반 인증
- **알고리즘**: HS256 (HMAC with SHA-256)
- **라이브러리**: python-jose[cryptography], passlib[bcrypt]
- **토큰 구조**: 
  ```json
  {
    "sub": "username",
    "exp": 1640995200,
    "iat": 1640991600
  }
  ```
- **비밀번호 해싱**: BCrypt 12 rounds
- **토큰 유효기간**: 30분 (환경변수로 조정 가능)

### 12.2 인증 구현 세부사항
- **HTTPBearer 보안 스킴**: FastAPI 표준 보안 방식
- **선택적 인증**: 개발 모드에서 인증 우회 가능
- **토큰 검증**: 모든 보호된 엔드포인트에서 자동 검증
- **에러 처리**: 401 Unauthorized 표준 응답

### 12.3 하드웨어 모니터링 보안
- **nvidia-smi 실행**: Docker 컨테이너 내에서 안전하게 실행
- **권한 관리**: 필요 최소 권한으로 GPU 정보 접근
- **서비스 실패 처리**: GPU 정보 수집 실패 시 서비스 중단

### 12.4 기존 보안 정책
- TLS(운영), 토큰 기반 인증, CORS 화이트리스트
- 입력 검증·금칙어 필터, 로그 마스킹, 데이터 보존 정책

---

## 13) 테스트 전략 및 서비스 검증

### 13.1 기본 테스트 전략
- 단위: 스키마/검증/핵심 유틸
- 통합: `/v1/chat/completions` 정상/스트리밍/에러
- 부하: k6/vegeta로 동시 1→5→10, 5분(p50/p95/에러율)
- 회귀: 모델·파라미터 변경 시 자동 벤치 실행

### 13.2 서비스 연결 검증 결과 (2025년 8월 실행)

#### 헬스 체크 검증
```bash
curl http://localhost:8080/health
# ✅ 성공: {"status":"healthy","service":"vLLM Chat Gateway","version":"1.0.0"}
```

#### JWT 인증 검증 (수정된 엔드포인트)
```bash
# 토큰 발급 (올바른 엔드포인트와 비밀번호)
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# ✅ 성공: {"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","token_type":"bearer"}

# vLLM 직접 테스트
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-ai/DeepSeek-R1-Distill-Qwen-14B","messages":[{"role":"user","content":"안녕하세요"}],"max_tokens":50}'
# ✅ 성공: 채팅 완성 응답 수신
```

#### 보호된 API 엔드포인트 검증
```bash
# 채팅 API (인증 필요)
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"model":"deepseek-ai/DeepSeek-R1-Distill-Qwen-14B","messages":[{"role":"user","content":"테스트"}],"max_tokens":30}'
# ✅ 성공: SSE 스트림 응답

# 인증 없이 접근 시도
curl http://localhost:8080/api/chat -d '{}'
# ✅ 예상대로 401 Unauthorized 반환
```

#### 하드웨어 모니터링 검증
- ✅ Gateway 컨테이너에서 nvidia-smi 실행 성공
- ✅ GPU 사용률: GPU0/GPU1 각각 87% (21GB/24GB) 
- ✅ vLLM 모델 정상 로딩 및 응답 확인

### 13.3 검증된 기능 목록
- [x] JWT 기반 인증 시스템
- [x] 토큰 발급 및 검증
- [x] 보호된 API 엔드포인트 접근 제어
- [x] 개발 모드 인증 우회
- [x] Docker 컨테이너 nvidia-smi 통합
- [x] 서비스 간 연결성
- [x] 하드웨어 모니터링 및 서비스 실패 처리

---

## 14) 일정 · 마일스톤

**Sprint 1** — MVP 가동: vLLM compose, Gateway 최소 기능, 프론트 연동, 초기 부하/튜닝

**Sprint 2** — 저장/관측: Postgres 연동, 사용량 메트릭 적재, 간단 대시보드

**Sprint 3** — 운영화: Nginx/TLS/CORS, 레이트리밋, 운영 가이드/장애 대응 룰북

---

## 15) 운영 정책(장애·변경·백업)

- 장애: 표준 에러 바디/재시도 가이드, on-call 절차, 로그/트레이스 확보
- 변경: 버전 고정·릴리스 노트·롤백 스위치
- 백업/DR: DB 백업 주기, 로그 보관, 단일 노드 DR 가이드(스냅샷)

---

## 16) 리스크 & 대응

- VRAM/OOM → 컨텍스트·유틸 조정, 양자화·swap 활용
- 모델/의존성 드리프트 → 버전 고정, 재현 가능한 빌드
- 요청 폭주 → 게이트웨이 큐잉·429·백오프
- 프롬프트 인젝션 → 정책·필터·시스템 프롬프트 설계 강화

---

## 17) 부록

### 17-A. docker-compose 스켈레톤(개발용)

```yaml
version: '3.9'
services:
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm-server
    restart: unless-stopped
    ports: ['8000:8000']
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    command: >
      --model ${MODEL_ID}
      --dtype float16
      --max-model-len ${VLLM_MAXLEN}
      --tensor-parallel-size ${VLLM_TP}
      --gpu-memory-utilization ${VLLM_UTIL}
      --host 0.0.0.0
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
  gateway:
    build: ./gateway
    environment:
      - VLLM_BASE_URL=http://vllm:8000/v1
      - JWT_SECRET=${JWT_SECRET}
    ports: ['8080:8080']
    depends_on: [vllm]
  frontend:
    build: ./frontend
    environment:
      - VITE_API_BASE=http://gateway:8080
    ports: ['3000:3000']
    depends_on: [gateway]
  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports: ['5432:5432']
  redis:
    image: redis:7-alpine
    command: redis-server --save "" --appendonly no
    ports: ['6379:6379']
volumes:
  pgdata: {}
```

### 17-B. Nginx(SSE) 리버스 프록시 예시

```nginx
location /v1/ {
  proxy_pass http://vllm:8000;
  proxy_http_version 1.1;
  proxy_set_header Connection "";
  proxy_buffering off;
  proxy_cache off;
  proxy_read_timeout 3600s;
  chunked_transfer_encoding on;
  add_header X-Accel-Buffering no;
  add_header Access-Control-Allow-Origin $http_origin always;
  add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
  add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
  if ($request_method = OPTIONS) { return 204; }
}
```

### 17-C. 벤치마크 스크립트(예시)

```bash
# vegeta
echo '{"model":"...","messages":[{"role":"user","content":"ping"}]}' \
| vegeta attack -duration=60s -rate=30 -targets=<(echo "POST http://localhost:8000/v1/chat/completions
Content-Type: application/json") \
| vegeta report
# k6: 동시 1→5→10 단계 시나리오 작성
```

---

## 🚀 시스템 관리 (Quick Start)

### 빠른 시작/정지
```bash
# 시스템 시작
./start

# 시스템 정지
./stop

# 상태 확인
./status
```

### 상세 관리 스크립트
```bash
# 전체 시스템 관리
./scripts/start.sh        # 시스템 시작 (상세 출력)
./scripts/stop.sh         # 시스템 정지
./scripts/restart.sh      # 시스템 재시작
./scripts/cleanup.sh      # 완전 정리 (데이터 삭제 주의!)

# 모니터링 및 디버깅
./scripts/status.sh       # 시스템 상태, GPU 사용량, 리소스 확인
./scripts/logs.sh         # 전체 로그 확인
./scripts/logs.sh vllm    # 특정 서비스 로그 확인
./scripts/logs.sh gateway # Gateway 로그 확인

# 성능 및 설치
./scripts/benchmark.sh    # 성능 벤치마크 테스트
./scripts/setup.sh        # 시스템 초기 설정
```

### 접속 정보
- **Frontend**: http://localhost:3000 (사용자 인터페이스)
- **Gateway API**: http://localhost:8080 (백엔드 API) 
- **vLLM API**: http://localhost:8000 (모델 API)
- **nginx Proxy**: http://localhost:80 (통합 게이트웨이)

### Docker Compose 직접 사용
```bash
# 환경 파일과 함께 실행
sg docker -c "docker-compose --env-file .env.local up -d"
sg docker -c "docker-compose --env-file .env.local down"
sg docker -c "docker-compose --env-file .env.local logs --follow vllm"
```

---

## 변경 이력

- **v1.3 (2025-01-27)**: 🆕 **배포 완료 및 시스템 검증** - 전체 서비스 정상 작동 확인, AI 채팅 기능 검증, GPU 모니터링 활성화
- **v1.2 (2025-01-27)**: 🆕 **배포 로그 및 시스템 상태 문서화** - 실시간 모니터링 정보, 성능 메트릭, 운영 체크리스트 추가
- **v1.1 (2025-08-16)**: SW 서비스 개발기획 일반 구조에 맞춰 **재작성**, 섹션/번호 체계 정비, 운영·보안·성능 가이드 정돈
- **v1.0**: 초기 초안 정리(MVP 범위/아키텍처/배포/튜닝/보안/테스트/로드맵)

---

## 📚 추가 문서 가이드

### **개발자를 위한 상세 가이드**
- **[개발자 온보딩 가이드](./DEVELOPER_ONBOARDING.md)** 🆕 - 새 팀원을 위한 5일 완성 가이드
- **[테스트 가이드](./TESTING_GUIDE.md)** 🆕 - 포괄적인 테스트 전략 및 실행 방법
- **[Gateway 개발 가이드](./gateway/GATEWAY_GUIDE.md)** - FastAPI 백엔드 및 모델 관리 API
- **[Frontend 개발 가이드](./frontend/FRONTEND_GUIDE.md)** - React + TypeScript 프론트엔드

### **운영자를 위한 실무 가이드**  
- **[운영 가이드](./OPERATIONS.md)** - 일상 운영, 모니터링, 문제 해결
- **[모델 관리 가이드](./MODEL_MANAGEMENT.md)** - 프로파일 기반 모델 전환 시스템
- **[시작 가이드](./GETTING_STARTED.md)** - 빠른 설치 및 실행 방법
- **[배포 로그](./DEPLOYMENT_LOG.md)** 🆕 - 최근 배포 작업 내역 및 검증 결과
- **[시스템 상태](./SYSTEM_STATUS.md)** 🆕 - 실시간 모니터링 정보 및 성능 메트릭
- **[작업 완료 요약](./COMPLETION_SUMMARY.md)** 🆕 - 전체 작업 수행 내역 및 성과 요약

### **시스템 이해를 위한 문서**
- **[아키텍처 가이드](./ARCHITECTURE.md)** - 시스템 설계 및 기술적 결정 사항
- **[성능 테스트 가이드](./k6/K6_GUIDE.md)** - 부하 테스트 및 성능 최적화
- **[시스템 관리 스크립트](./scripts/README.md)** 🆕 - 자동화 도구 및 유틸리티 상세 가이드

> **💡 문서 읽기 권장 순서**: README → GETTING_STARTED → DEVELOPER_ONBOARDING → 각 모듈별 가이드
