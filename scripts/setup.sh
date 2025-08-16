#!/bin/bash
set -e

echo "🚀 vLLM 서비스 설치 및 설정 시작..."

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수: 메시지 출력
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 시스템 요구사항 확인
print_status "시스템 요구사항 확인 중..."

# NVIDIA GPU 확인
if ! command -v nvidia-smi &> /dev/null; then
    print_error "NVIDIA GPU 드라이버가 설치되지 않았습니다."
    exit 1
fi
print_success "NVIDIA GPU 감지됨"

# Docker 확인
if ! command -v docker &> /dev/null; then
    print_error "Docker가 설치되지 않았습니다."
    print_status "Ubuntu에서 Docker 설치: https://docs.docker.com/engine/install/ubuntu/"
    exit 1
fi
print_success "Docker 감지됨: $(docker --version)"

# Docker Compose 확인
if ! command -v docker compose &> /dev/null; then
    print_error "Docker Compose가 설치되지 않았습니다."
    exit 1
fi
print_success "Docker Compose 감지됨: $(docker compose version)"

# NVIDIA Container Toolkit 확인
print_status "NVIDIA Container Toolkit 확인 중..."
if docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi > /dev/null 2>&1; then
    print_success "NVIDIA Container Toolkit 작동 중"
else
    print_warning "NVIDIA Container Toolkit 설정 필요"
    print_status "설치 중..."
    
    # NVIDIA Container Toolkit 설치
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
        && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
        && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo systemctl restart docker
    
    # 다시 테스트
    if docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi > /dev/null 2>&1; then
        print_success "NVIDIA Container Toolkit 설치 완료"
    else
        print_error "NVIDIA Container Toolkit 설치 실패"
        exit 1
    fi
fi

# 환경변수 파일 확인
print_status "환경변수 파일 확인 중..."
if [ ! -f .env.local ]; then
    print_warning ".env.local 파일이 없습니다. .env.sample에서 복사합니다."
    cp .env.sample .env.local
    print_warning "⚠️  .env.local 파일을 수정한 후 다시 실행하세요!"
    print_status "필수 설정 항목:"
    print_status "  - HUGGING_FACE_HUB_TOKEN (Hugging Face 토큰)"
    print_status "  - JWT_SECRET (JWT 암호화 키)"
    print_status "  - POSTGRES_PASSWORD (데이터베이스 비밀번호)"
    exit 1
fi
print_success "환경변수 파일 확인 완료"

# 환경변수 로드
source .env.local

# Hugging Face 토큰 확인
if [ -z "$HUGGING_FACE_HUB_TOKEN" ]; then
    print_warning "HUGGING_FACE_HUB_TOKEN이 설정되지 않았습니다."
    print_status "일부 모델의 경우 Hugging Face 토큰이 필요할 수 있습니다."
fi

# Docker 네트워크 생성
print_status "Docker 네트워크 생성 중..."
docker network create vllm_network || print_warning "네트워크가 이미 존재합니다"

# 모델 캐시 디렉토리 생성
print_status "모델 캐시 디렉토리 생성 중..."
mkdir -p ~/.cache/huggingface
mkdir -p ./models

# Docker 이미지 빌드
print_status "Docker 이미지 빌드 중..."
docker compose build --no-cache

# 데이터베이스 초기화
print_status "데이터베이스 초기화 중..."
docker compose up -d postgres redis
print_status "데이터베이스 준비 대기 (30초)..."
sleep 30

# 데이터베이스 테이블 생성
if [ -f scripts/init.sql ]; then
    print_status "데이터베이스 스키마 생성 중..."
    docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /docker-entrypoint-initdb.d/init.sql
    print_success "데이터베이스 스키마 생성 완료"
fi

# 서비스 시작
print_status "서비스 시작 중..."
docker compose up -d

# 헬스체크 대기
print_status "서비스 준비 대기 중 (최대 5분)..."
timeout 300 bash -c '
    until curl -f http://localhost:8080/health > /dev/null 2>&1; do
        echo "Gateway 준비 대기 중..."
        sleep 10
    done
'

if [ $? -eq 0 ]; then
    print_success "Gateway 서비스 준비 완료"
else
    print_error "Gateway 서비스 시작 실패"
    print_status "로그를 확인하세요: docker compose logs gateway"
    exit 1
fi

# Frontend 확인
timeout 60 bash -c '
    until curl -f http://localhost:3000 > /dev/null 2>&1; do
        echo "Frontend 준비 대기 중..."
        sleep 5
    done
'

if [ $? -eq 0 ]; then
    print_success "Frontend 서비스 준비 완료"
else
    print_warning "Frontend 서비스 준비 지연"
fi

# vLLM 서비스 확인 (더 긴 대기 시간)
print_status "vLLM 서비스 준비 대기 중 (최대 10분)..."
timeout 600 bash -c '
    until curl -f http://localhost:8000/v1/models > /dev/null 2>&1; do
        echo "vLLM 모델 로딩 대기 중..."
        sleep 15
    done
'

if [ $? -eq 0 ]; then
    print_success "vLLM 서비스 준비 완료"
else
    print_warning "vLLM 서비스 준비 지연 - 모델 로딩에 시간이 걸릴 수 있습니다"
    print_status "로그를 확인하세요: docker compose logs vllm"
fi

print_success "🎉 vLLM 서비스 설치 완료!"
echo ""
print_status "서비스 접속 정보:"
print_status "  - Frontend: http://localhost:3000"
print_status "  - API Gateway: http://localhost:8080"
print_status "  - API 문서: http://localhost:8080/docs"
print_status "  - vLLM API: http://localhost:8000"
print_status "  - 데이터베이스 관리: http://localhost:8081 (Adminer)"
echo ""
print_status "서비스 상태 확인: docker compose ps"
print_status "로그 확인: docker compose logs -f [service-name]"
print_status "서비스 중지: docker compose down"
