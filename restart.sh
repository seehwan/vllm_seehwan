#!/bin/bash
# vLLM 챗봇 시스템 재시작 스크립트

echo "🔄 vLLM 챗봇 시스템을 재시작합니다..."

# 정지 후 시작
sg docker -c "docker-compose --env-file .env.local restart"

echo "✅ 시스템이 재시작되었습니다."
echo ""
echo "📋 서비스 상태 확인:"
sleep 3
sg docker -c "docker-compose --env-file .env.local ps"
