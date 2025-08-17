#!/bin/bash
# vLLM 챗봇 시스템 완전 정리 스크립트

echo "🗑️  vLLM 챗봇 시스템을 완전히 정리합니다..."
echo "⚠️  이 작업은 모든 데이터와 볼륨을 삭제합니다!"

read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 취소되었습니다."
    exit 1
fi

# 모든 서비스 정지 및 데이터 삭제
sg docker -c "docker-compose --env-file .env.local down --volumes --remove-orphans"

# Docker 이미지 정리 (선택사항)
read -p "Docker 이미지도 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sg docker -c "docker system prune -af"
    echo "🧹 Docker 이미지까지 정리되었습니다."
fi

echo "✅ 시스템이 완전히 정리되었습니다."
echo ""
echo "🚀 새로 시작하려면: ./start.sh"
