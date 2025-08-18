#!/bin/bash

# vLLM 챗봇 서비스 관리 스크립트 (.env.local 사용)

case "$1" in
    start)
        echo "🚀 서비스 시작 중..."
        docker-compose --env-file .env.local up -d
        ;;
    stop)
        echo "🛑 서비스 정지 중..."
        docker-compose --env-file .env.local down
        ;;
    restart)
        echo "🔄 서비스 재시작 중..."
        docker-compose --env-file .env.local down
        docker-compose --env-file .env.local up -d
        ;;
    status)
        echo "📊 서비스 상태:"
        docker-compose --env-file .env.local ps
        ;;
    logs)
        if [ -z "$2" ]; then
            docker-compose --env-file .env.local logs -f
        else
            docker-compose --env-file .env.local logs -f "$2"
        fi
        ;;
    *)
        echo "사용법: $0 {start|stop|restart|status|logs [service]}"
        echo "예시:"
        echo "  $0 start    - 모든 서비스 시작"
        echo "  $0 stop     - 모든 서비스 정지"
        echo "  $0 restart  - 모든 서비스 재시작"
        echo "  $0 status   - 서비스 상태 확인"
        echo "  $0 logs     - 모든 서비스 로그"
        echo "  $0 logs gateway - 특정 서비스 로그"
        exit 1
        ;;
esac
