#!/bin/bash
# vLLM 챗봇 시스템 정지 스크립트

echo "🛑 vLLM 챗봇 시스템을 정지합니다..."

# Docker 그룹 권한으로 실행
sg docker -c "docker-compose --env-file .env.local down"

echo "✅ 모든 서비스가 정지되었습니다."
echo ""
echo "🗂️ 데이터 및 볼륨 완전 삭제: ./cleanup.sh"
echo "🚀 시스템 재시작: ./start.sh"
