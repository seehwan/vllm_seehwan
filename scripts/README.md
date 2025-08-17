# 🛠️ Scripts 디렉토리

vLLM 챗봇 시스템 관리를 위한 스크립트들이 포함되어 있습니다.

## 📋 스크립트 목록

### 시스템 관리 스크립트
- **`start.sh`** - 전체 시스템 시작
- **`stop.sh`** - 전체 시스템 정지  
- **`restart.sh`** - 전체 시스템 재시작
- **`status.sh`** - 시스템 상태 확인
- **`logs.sh`** - 로그 확인
- **`cleanup.sh`** - 완전 정리 (데이터 삭제)

### 설치 및 벤치마크 스크립트
- **`setup.sh`** - 시스템 초기 설정
- **`benchmark.sh`** - 성능 벤치마크 테스트
- **`init.sql`** - 데이터베이스 초기화 SQL

## 🚀 빠른 사용법

### 프로젝트 루트에서 사용 (권장)
```bash
# 시스템 시작
./start

# 시스템 정지  
./stop

# 상태 확인
./status
```

### scripts 디렉토리에서 직접 사용
```bash
# 시스템 시작
./scripts/start.sh

# 로그 확인 (전체)
./scripts/logs.sh

# 특정 서비스 로그 확인
./scripts/logs.sh vllm
./scripts/logs.sh gateway

# 시스템 재시작
./scripts/restart.sh

# 완전 정리 (주의: 데이터 삭제)
./scripts/cleanup.sh
```

## 📝 스크립트 상세 내용

### start.sh
```bash
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
```

### stop.sh
```bash
#!/bin/bash
# vLLM 챗봇 시스템 정지 스크립트

echo "🛑 vLLM 챗봇 시스템을 정지합니다..."

# Docker 그룹 권한으로 실행
sg docker -c "docker-compose --env-file .env.local down"

echo "✅ 모든 서비스가 정지되었습니다."
echo ""
echo "🗂️ 데이터 및 볼륨 완전 삭제: ./cleanup.sh"
echo "🚀 시스템 재시작: ./start.sh"
```

### restart.sh
```bash
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
```

### status.sh
```bash
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
```

### logs.sh
```bash
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
```

### cleanup.sh
```bash
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
```

## 📚 기존 스크립트들

### setup.sh
시스템 초기 설정 및 의존성 설치를 수행합니다.

### benchmark.sh  
시스템 성능 벤치마크를 실행합니다.

### init.sql
PostgreSQL 데이터베이스 초기화를 위한 SQL 스크립트입니다.

## ⚠️ 사용 주의사항

1. **권한 설정**: 모든 .sh 스크립트는 실행 권한이 필요합니다.
2. **Docker 권한**: sg docker 명령어로 Docker 그룹 권한이 필요합니다.
3. **환경 변수**: .env.local 파일의 환경 변수에 의존합니다.
4. **GPU 요구사항**: NVIDIA GPU 및 드라이버가 필요합니다.
