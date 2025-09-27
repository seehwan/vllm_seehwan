#!/bin/bash

# vLLM Chat 서비스 전체 시작 스크립트

echo "=== vLLM Chat 서비스 시작 ==="

# 환경 변수 로드
if [ -f ".env.clean" ]; then
    echo "환경 변수 로드 중..."
    export $(cat .env.clean | xargs)
fi

# 백엔드 서비스 시작 (Docker)
echo "백엔드 서비스 시작 중..."
docker-compose up -d postgres redis gateway vllm

# 서비스 시작 대기
echo "서비스 시작 대기 중..."
sleep 10

# 서비스 상태 확인
echo "=== 서비스 상태 확인 ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

# Gateway Health Check
echo "=== Gateway Health Check ==="
curl -s http://localhost:8080/health | jq || echo "Gateway 연결 실패"

# 프론트엔드 시작
echo "=== 프론트엔드 시작 ==="
echo "프론트엔드는 별도 터미널에서 실행하세요:"
echo "  ./start-frontend.sh"
echo ""
echo "접속 주소:"
echo "  프론트엔드: https://localhost:3000"
echo "  Gateway API: http://localhost:8080"
echo "  vLLM API: http://localhost:8000"
