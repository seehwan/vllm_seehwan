# Scripts

vLLM 챗봇 서비스의 유틸리티 스크립트 모음입니다.

## 📋 스크립트 목록

### 🚀 setup.sh

**자동 설치 및 설정 스크립트**

전체 서비스를 자동으로 설치하고 구성하는 메인 스크립트입니다.

```bash
# 실행
./scripts/setup.sh
```

**기능:**

- 시스템 요구사항 검증 (NVIDIA GPU, Docker, NVIDIA Container Toolkit)
- 환경변수 설정 확인
- Docker 이미지 빌드
- 데이터베이스 초기화
- 서비스 시작 및 헬스체크
- 설치 완료 안내

**검증 항목:**

- NVIDIA GPU 드라이버 (535+)
- Docker 엔진 (24.x+)
- Docker Compose v2
- NVIDIA Container Toolkit

### 📊 benchmark.sh

**성능 벤치마크 스크립트**

시스템 성능을 종합적으로 측정하는 벤치마크 도구입니다.

```bash
# 실행
./scripts/benchmark.sh
```

**측정 항목:**

- **K6 부하 테스트**: 동시 사용자별 성능 측정
- **스트리밍 테스트**: SSE 스트리밍 성능 분석
- **지연 시간 테스트**: 단일 요청 응답 시간
- **동시성 테스트**: 동시 요청 처리 성능
- **Vegeta 처리량 테스트**: RPS 및 처리량 측정

**모니터링:**

- GPU 사용률 및 메모리 사용량
- 시스템 CPU/메모리 사용률
- 네트워크 I/O 통계

**결과 파일:**

```
benchmark_results_YYYYMMDD_HHMMSS/
├── benchmark_summary.md         # 종합 요약
├── load_test_results.json      # K6 부하 테스트
├── streaming_test_results.json # 스트리밍 테스트
├── latency_test.txt           # 지연 시간 테스트
├── concurrent_test.txt        # 동시성 테스트
├── gpu_stats.csv             # GPU 모니터링
├── system_stats.csv          # 시스템 모니터링
├── vegeta_results.bin        # Vegeta 원시 데이터
├── vegeta_report.txt         # Vegeta 보고서
└── vegeta_plot.html          # Vegeta 시각화
```

### 🗄️ init.sql

**데이터베이스 초기화 스크립트**

PostgreSQL 데이터베이스의 초기 스키마와 기본 데이터를 설정합니다.

**생성 테이블:**

- `users` - 사용자 정보
- `conversations` - 대화 세션
- `messages` - 메시지 내역
- `request_logs` - API 요청 로그
- `user_sessions` - 사용자 세션 관리

**기본 데이터:**

- 관리자 계정: `admin@example.com` (비밀번호: `admin123`)
- 테스트 계정: `test@example.com` (비밀번호: `test123`)

**인덱스 최적화:**

- 대화 검색 성능 향상
- 메시지 조회 최적화
- 로그 분석 성능 개선

## 🔧 스크립트 실행 가이드

### 환경 준비

```bash
# 모든 스크립트에 실행 권한 부여
chmod +x scripts/*.sh

# 환경변수 파일 준비
cp .env.sample .env.local
# .env.local 편집 필요
```

### 단계별 실행

#### 1. 초기 설치

```bash
# 전체 시스템 설치
./scripts/setup.sh
```

#### 2. 성능 검증

```bash
# 벤치마크 실행 (서비스 실행 후)
./scripts/benchmark.sh
```

#### 3. 데이터베이스 재초기화 (필요시)

```bash
# 컨테이너에서 직접 실행
docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /docker-entrypoint-initdb.d/init.sql
```

## 🔍 모니터링 및 진단

### 서비스 상태 확인

```bash
# 전체 서비스 상태
docker compose ps

# 특정 서비스 로그
docker compose logs -f [service-name]

# 헬스체크
curl http://localhost:8080/health
curl http://localhost:8000/v1/models
```

### 성능 모니터링

```bash
# GPU 실시간 모니터링
nvidia-smi -l 5

# 시스템 리소스 확인
htop
docker stats

# 네트워크 확인
netstat -tlnp | grep -E "(3000|8000|8080)"
```

### 벤치마크 결과 분석

```bash
# 최신 벤치마크 결과 확인
ls -la benchmark_results_*/

# 요약 보고서 보기
cat benchmark_results_*/benchmark_summary.md

# K6 테스트 결과 상세 분석
cat benchmark_results_*/load_test_summary.txt | grep -A 10 'checks'

# GPU 사용률 트렌드
tail -20 benchmark_results_*/gpu_stats.csv
```

## ⚙️ 스크립트 커스터마이징

### setup.sh 수정

**타임아웃 조정:**

```bash
# vLLM 준비 대기 시간 (기본 10분)
timeout 600 bash -c 'until curl -f http://localhost:8000/v1/models; do sleep 15; done'

# 더 긴 대기가 필요한 경우
timeout 1200 bash -c '...'  # 20분으로 증가
```

**GPU 설정 확인:**

```bash
# 특정 GPU만 사용하도록 제한
export CUDA_VISIBLE_DEVICES=1
```

### benchmark.sh 수정

**테스트 시나리오 조정:**

```bash
# 동시 사용자 수 변경
for CONCURRENT in 1 3 5 10 20; do  # 20명까지 확장
    # ...
done

# 테스트 시간 조정
vegeta attack -duration=120s -rate=30  # 2분으로 증가
```

**모니터링 간격 조정:**

```bash
# GPU 모니터링 간격 (기본 5초)
nvidia-smi --query-gpu=... -l 10  # 10초로 변경
```

## 🐛 문제 해결

### 일반적인 오류

#### 1. setup.sh 실행 실패

**NVIDIA Container Toolkit 오류:**

```bash
# 수동 설치
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 테스트
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

**권한 오류:**

```bash
# Docker 권한 확인
sudo usermod -aG docker $USER
newgrp docker
```

#### 2. benchmark.sh 실행 실패

**K6 설치 실패:**

```bash
# 수동 설치
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**Vegeta 설치:**

```bash
# Go를 통한 설치
go install github.com/tsenart/vegeta@latest

# 또는 바이너리 다운로드
wget https://github.com/tsenart/vegeta/releases/latest/download/vegeta_linux_amd64.tar.gz
tar -xzf vegeta_linux_amd64.tar.gz
sudo mv vegeta /usr/local/bin/
```

#### 3. 데이터베이스 초기화 실패

```bash
# PostgreSQL 연결 확인
docker compose exec postgres pg_isready

# 수동 실행
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

# 스키마 확인
\dt  # 테이블 목록
\d users  # users 테이블 구조
```

### 로그 분석

```bash
# setup.sh 로그 저장
./scripts/setup.sh 2>&1 | tee setup.log

# benchmark.sh 로그 저장
./scripts/benchmark.sh 2>&1 | tee benchmark.log

# 에러만 필터링
grep -i error setup.log
grep -i failed benchmark.log
```

## 📝 추가 스크립트 작성 가이드

### 새 스크립트 추가

```bash
# 스크립트 템플릿
#!/bin/bash
set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 메인 로직
main() {
    print_status "스크립트 시작..."
    # 실제 작업 수행
    print_success "스크립트 완료!"
}

main "$@"
```

### 스크립트 모범 사례

1. **오류 처리**: `set -e`로 오류 시 즉시 종료
2. **색상 출력**: 사용자 친화적인 메시지
3. **상태 확인**: 선행 조건 검증
4. **로그 기록**: 중요한 작업 결과 저장
5. **리소스 정리**: 임시 파일, 프로세스 정리

이제 모든 스크립트가 체계적으로 관리되며, 각각의 역할과 사용법이 명확해졌습니다!
