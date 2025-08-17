#!/bin/bash
# vLLM 챗봇 시스템 상태 확인 스크립트

echo "📊 vLLM 챗봇 시스템 상태"
echo "======================="

echo ""
echo "🐳 Docker 컨테이너 상태:"
sg docker -c "docker-compose --env-file .env.local ps"

echo ""
echo "🎮 GPU 사용량:"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits

echo ""
echo "🌐 서비스 Health Check:"
echo "  Gateway:  $(curl -s http://localhost:8080/health | grep -o '"status":"[^"]*"' || echo '❌ 연결 실패')"

echo ""
echo "📈 시스템 리소스:"
echo "  Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo "  CPU:    $(top -bn1 | grep load | awk '{print $10,$11,$12}')"

echo ""
echo "🔧 관리 명령어:"
echo "  시작:      ./start.sh"
echo "  정지:      ./stop.sh" 
echo "  재시작:    ./restart.sh"
echo "  로그:      ./logs.sh [서비스명]"
