#!/bin/bash
# vLLM 챗봇 시스템 시작 스크립트

echo "🚀 vLLM 챗봇 시스템을 시작합니다..."

# Docker 그룹 권한으로 실행
sg docker -c "docker-compose --env-file .env.local up -d"

echo "✅ 시스템이 백그라운드에서 시작되었습니다."
echo ""
echo "📋 서비스 상태 확인:"
sleep 3
sg docker -c "docker-compose --env-file .env.local ps"

echo ""
echo "🌐 접속 정보:"
echo "  - Frontend:  http://localhost:3000"
echo "  - Gateway:   http://localhost:8080"
echo "  - vLLM API:  http://localhost:8000"
echo "  - nginx:     http://localhost:80"
echo ""
echo "📝 로그 확인: ./logs.sh"
echo "🛑 시스템 정지: ./stop.sh"
