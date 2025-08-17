# vLLM Chat Gateway

FastAPI 기반의 vLLM 챗봇 서비스 API 게이트웨이입니다.

## 🛠 기술 스택

- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Database**: PostgreSQL (AsyncPG)
- **Cache**: Redis
- **Authentication**: JWT (python-jose)
- **Rate Limiting**: SlowAPI
- **Logging**: Structlog
- **Migration**: Alembic (SQLAlchemy 2.0)
- **Monitoring**: Prometheus Client

## 📦 주요 의존성

```python
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
pydantic>=2.5.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
redis>=5.0.0
python-jose[cryptography]>=3.3.0
structlog>=23.2.0
```

## 🚀 개발 환경 실행

### 필수 요구사항

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- vLLM 서버 (http://localhost:8000)

### 로컬 개발 서버 실행

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
cp ../.env.sample ../.env.local
# .env.local 파일 편집

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Docker 환경에서 실행

```bash
# 프로젝트 루트에서 실행
docker compose -f docker-compose.yml -f docker-compose.dev.yml up gateway
```

## 🏗 아키텍처

### 디렉토리 구조

```
gateway/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 설정 관리
│   ├── database.py          # 데이터베이스 연결
│   ├── dependencies.py      # 의존성 주입
│   ├── middleware.py        # 커스텀 미들웨어
│   ├── auth/               # 인증 관련
│   │   ├── __init__.py
│   │   ├── jwt.py          # JWT 토큰 처리
│   │   ├── models.py       # 인증 모델
│   │   └── utils.py        # 인증 유틸리티
│   ├── models/             # SQLAlchemy 모델
│   │   ├── __init__.py
│   │   ├── base.py         # 베이스 모델
│   │   ├── user.py         # 사용자 모델
│   │   ├── conversation.py # 대화 모델
│   │   └── message.py      # 메시지 모델
│   ├── routers/            # API 라우터
│   │   ├── __init__.py
│   │   ├── auth.py         # 인증 API
│   │   ├── chat.py         # 채팅 API
│   │   ├── conversations.py # 대화 관리 API
│   │   └── health.py       # 헬스체크
│   ├── services/           # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── chat_service.py # 채팅 서비스
│   │   ├── user_service.py # 사용자 서비스
│   │   └── vllm_client.py  # vLLM 클라이언트
│   ├── schemas/            # Pydantic 스키마
│   │   ├── __init__.py
│   │   ├── chat.py         # 채팅 스키마
│   │   ├── user.py         # 사용자 스키마
│   │   └── common.py       # 공통 스키마
│   └── utils/              # 유틸리티
│       ├── __init__.py
│       ├── logging.py      # 로깅 설정
│       ├── redis.py        # Redis 유틸리티
│       └── rate_limit.py   # 레이트 리밋
├── alembic/               # 데이터베이스 마이그레이션
├── tests/                 # 테스트 코드
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── README.md
```

### 주요 컴포넌트

#### 1. API 게이트웨이

- vLLM OpenAI 호환 API와 프록시 역할
- 요청/응답 변환 및 검증
- SSE 스트리밍 지원

#### 2. 인증 시스템

- JWT 토큰 기반 인증
- 사용자 권한 관리 (user, admin)
- 토큰 갱신 및 만료 처리

#### 3. 레이트 리밋

- Redis 기반 레이트 리밋
- 사용자별, IP별 제한
- 동적 제한 설정 지원

#### 4. 로깅 및 모니터링

- 구조화된 로깅 (Structlog)
- 요청 추적 (Request ID)
- Prometheus 메트릭 수집

## 🔌 API 엔드포인트

### 인증 API

```
POST /api/auth/register    # 사용자 등록
POST /api/auth/login       # 로그인
POST /api/auth/refresh     # 토큰 갱신
POST /api/auth/logout      # 로그아웃
GET  /api/auth/me          # 사용자 정보
```

### 채팅 API

```
POST /api/chat             # 채팅 스트리밍 (SSE)
POST /api/chat/completions # 일반 채팅 (non-streaming)
GET  /api/models           # 사용 가능한 모델 목록
```

### 대화 관리 API

```
GET    /api/conversations           # 대화 목록
POST   /api/conversations           # 새 대화 생성
GET    /api/conversations/{id}      # 대화 상세
PUT    /api/conversations/{id}      # 대화 수정
DELETE /api/conversations/{id}      # 대화 삭제
GET    /api/conversations/{id}/messages # 메시지 목록
```

### 시스템 API

```
GET /health                # 헬스체크
GET /metrics               # Prometheus 메트릭
GET /docs                  # API 문서 (개발 모드)
```

## ⚙️ 설정

### 환경변수 (.env.local)

```bash
# vLLM 설정
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=

# 보안 설정
JWT_SECRET=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# 데이터베이스
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/chatdb

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# 레이트 리밋
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# 로깅
LOG_LEVEL=INFO
```

### 설정 클래스 (`app/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "vLLM Chat Gateway"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # vLLM 설정
    VLLM_BASE_URL: str
    JWT_SECRET: str
    DATABASE_URL: str
    REDIS_URL: str

    class Config:
        env_file = ".env"
```

## 🧪 테스트

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html

# 특정 테스트 파일
pytest tests/test_chat.py -v

# 통합 테스트
pytest tests/integration/ -v
```

### 테스트 구조

```
tests/
├── unit/              # 단위 테스트
│   ├── test_auth.py   # 인증 테스트
│   ├── test_chat.py   # 채팅 테스트
│   └── test_models.py # 모델 테스트
├── integration/       # 통합 테스트
│   ├── test_api.py    # API 통합 테스트
│   └── test_vllm.py   # vLLM 연동 테스트
├── fixtures/          # 테스트 픽스처
└── conftest.py        # pytest 설정
```

## 📊 모니터링

### 로깅

```python
import structlog

logger = structlog.get_logger()

# 요청 로깅
logger.info("Chat request received",
           user_id=user.id,
           model=request.model,
           input_tokens=len(request.messages))
```

### 메트릭

```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('chat_requests_total',
                       'Total chat requests',
                       ['model', 'status'])
REQUEST_DURATION = Histogram('chat_request_duration_seconds',
                           'Chat request duration')
```

### 헬스체크

```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "vllm": await check_vllm_health(),
            "postgres": await check_db_health(),
            "redis": await check_redis_health()
        }
    }
```

## 🔒 보안

### 인증 플로우

1. 사용자 로그인 → JWT 토큰 발급
2. 요청 시 Bearer 토큰 검증
3. 토큰 만료 → 리프레시 토큰으로 갱신

### 보안 미들웨어

```python
# CORS 설정
app.add_middleware(CORSMiddleware,
                  allow_origins=settings.CORS_ORIGINS)

# 신뢰할 수 있는 호스트
app.add_middleware(TrustedHostMiddleware,
                  allowed_hosts=settings.ALLOWED_HOSTS)

# 레이트 리밋
app.add_middleware(RateLimitMiddleware)
```

### 입력 검증

```python
from pydantic import BaseModel, validator

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str
    temperature: Optional[float] = 0.7

    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0 or v > 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v
```

## 🚀 배포

### Docker 배포

```bash
# 이미지 빌드
docker build -t vllm-chat-gateway .

# 컨테이너 실행
docker run -p 8080:8080 \
  -e DATABASE_URL=... \
  -e REDIS_URL=... \
  vllm-chat-gateway
```

### 프로덕션 고려사항

1. **환경 분리**: 개발/스테이징/프로덕션 환경별 설정
2. **시크릿 관리**: JWT 시크릿, DB 비밀번호 등 안전한 저장
3. **로그 수집**: 중앙화된 로깅 시스템 연동
4. **백업**: 데이터베이스 정기 백업
5. **모니터링**: Grafana, Prometheus 연동

## 🐛 디버깅

### 로그 확인

```bash
# 개발 모드
uvicorn app.main:app --reload --log-level debug

# Docker 로그
docker compose logs -f gateway

# 특정 레벨 로그만
docker compose logs gateway | grep ERROR
```

### 일반적인 문제 해결

#### 1. vLLM 연결 실패

```bash
# vLLM 서버 상태 확인
curl http://localhost:8000/v1/models

# 네트워크 연결 확인
docker compose exec gateway ping vllm
```

#### 2. 데이터베이스 연결 실패

```bash
# PostgreSQL 연결 테스트
docker compose exec gateway pg_isready -h postgres

# 마이그레이션 확인
docker compose exec gateway alembic current
```

#### 3. Redis 연결 실패

```bash
# Redis 연결 테스트
docker compose exec gateway redis-cli -h redis ping
```

## 🔧 개발 가이드

### 새 API 엔드포인트 추가

1. `app/schemas/`에 Pydantic 스키마 정의
2. `app/models/`에 SQLAlchemy 모델 추가 (필요시)
3. `app/services/`에 비즈니스 로직 구현
4. `app/routers/`에 API 라우터 추가
5. `tests/`에 테스트 코드 작성

### 코드 품질 관리

```bash
# 코드 포매팅
black app/
ruff --fix app/

# 타입 검사
mypy app/

# 테스트 실행
pytest --cov=app
```

### 데이터베이스 마이그레이션

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "Add new table"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1
```

## 📞 문제 해결

자주 발생하는 문제들과 해결 방법:

1. **502 Bad Gateway**: vLLM 서버가 준비되지 않음 → 시간 대기 후 재시도
2. **Authentication Error**: JWT 토큰 만료 → 토큰 갱신 필요
3. **Rate Limit Exceeded**: 요청 제한 초과 → 잠시 대기 후 재시도
4. **Database Connection Error**: DB 연결 실패 → 연결 설정 확인
