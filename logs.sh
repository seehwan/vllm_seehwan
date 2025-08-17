#!/bin/bash
# vLLM 챗봇 시스템 로그 확인 스크립트

if [ -z "$1" ]; then
    echo "📋 전체 시스템 로그 (최근 20라인):"
    echo "================================="
    sg docker -c "docker-compose --env-file .env.local logs --tail=20"
else
    echo "📋 $1 서비스 로그:"
    echo "================"
    sg docker -c "docker-compose --env-file .env.local logs --tail=50 $1"
fi

echo ""
echo "🔧 사용법:"
echo "  전체 로그:     ./logs.sh"
echo "  특정 서비스:   ./logs.sh [서비스명]"
echo "    예: ./logs.sh vllm"
echo "    예: ./logs.sh gateway"
echo "    예: ./logs.sh frontend"
