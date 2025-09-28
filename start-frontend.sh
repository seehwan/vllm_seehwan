#!/bin/bash

# 프론트엔드 개발 서버 시작 스크립트

echo "=== vLLM Chat Frontend 시작 ==="

# 기존 프로세스 종료
echo "기존 프론트엔드 프로세스 종료 중..."
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

# 포트 정리
echo "포트 정리 중..."
sleep 2

# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치 (필요시)
if [ ! -d "node_modules" ]; then
    echo "의존성 설치 중..."
    npm install
fi

# 개발 서버 시작
echo "프론트엔드 개발 서버 시작 중..."
echo "접속 주소: https://localhost:3000"
echo "API 프록시: /api -> http://127.0.0.1:8080"

# 포트 3000에서 강제 실행
npm run dev:3000
