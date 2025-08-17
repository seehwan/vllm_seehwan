# 🚀 vLLM 챗봇 서비스 운영 가이드

이 문서는 vLLM 기반 챗봇 서비스의 일상적인 운영, 모니터링, 유지보수를 위한 실무 가이드입니다.

## 📊 일일 운영 체크리스트

### 🌅 아침 체크 (운영 시작)

```bash
# 1. 전체 서비스 상태 확인
docker compose ps

# 2. 헬스체크 수행
curl -f http://localhost:8080/health
curl -f http://localhost:8000/v1/models

# 3. GPU 상태 확인
nvidia-smi

# 4. 디스크 용량 확인
df -h

# 5. 메모리 사용량 확인
free -h

# 6. 지난 밤 에러 로그 확인
docker compose logs --since 24h | grep -i error
```

### 🌙 저녁 체크 (운영 종료 전)

```bash
# 1. 오늘 하루 사용량 통계
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
SELECT
    COUNT(*) as total_requests,
    AVG(latency_ms) as avg_latency,
    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as errors
FROM request_logs
WHERE created_at >= CURRENT_DATE;"

# 2. 로그 로테이션
docker compose logs --no-color > "logs/app_$(date +%Y%m%d).log"

# 3. 데이터베이스 백업
./scripts/backup_database.sh

# 4. GPU 온도 및 사용률 최종 확인
nvidia-smi
```

## 📈 모니터링 및 알림

### 핵심 지표 모니터링

#### 1. 성능 지표

```bash
# 응답 시간 모니터링
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
SELECT
    model,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms) as p50_latency,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency,
    AVG(latency_ms) as avg_latency
FROM request_logs
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY model;"
```

#### 2. 에러율 모니터링

```bash
# 시간대별 에러율 확인
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as errors,
    ROUND(COUNT(CASE WHEN status_code >= 400 THEN 1 END) * 100.0 / COUNT(*), 2) as error_rate
FROM request_logs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;"
```

#### 3. 리소스 사용률

```bash
# GPU 메모리 사용률 추적
#!/bin/bash
# monitor_gpu.sh
while true; do
    echo "$(date): $(nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits)"
    sleep 300  # 5분마다 체크
done >> gpu_usage.log &
```

### 알림 설정

#### Slack/Discord 웹훅 알림

```bash
# webhook_alert.sh
#!/bin/bash

WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
ALERT_LEVEL=$1
MESSAGE=$2

curl -X POST -H 'Content-type: application/json' \
    --data "{'text':'[$ALERT_LEVEL] vLLM Service Alert: $MESSAGE'}" \
    $WEBHOOK_URL
```

#### 자동 알림 조건

```bash
# auto_monitor.sh
#!/bin/bash

# GPU 메모리 사용률 90% 이상
GPU_USAGE=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F, '{print int($1/$2*100)}')
if [ $GPU_USAGE -gt 90 ]; then
    ./webhook_alert.sh "WARNING" "GPU memory usage: ${GPU_USAGE}%"
fi

# 에러율 5% 이상
ERROR_RATE=$(docker compose logs --since 1h gateway | grep "ERROR" | wc -l)
if [ $ERROR_RATE -gt 50 ]; then  # 1시간에 50개 이상 에러
    ./webhook_alert.sh "CRITICAL" "High error rate detected: $ERROR_RATE errors in last hour"
fi

# 디스크 사용률 85% 이상
DISK_USAGE=$(df -h / | awk 'NR==2{print int($5)}')
if [ $DISK_USAGE -gt 85 ]; then
    ./webhook_alert.sh "WARNING" "Disk usage: ${DISK_USAGE}%"
fi
```

## 🔧 유지보수 작업

### 🎯 모델 관리 운영 가이드 ⭐

#### **일상적인 모델 상태 모니터링**
```bash
#!/bin/bash
# model_health_check.sh

echo "🤖 모델 상태 점검: $(date)"

# 1. 현재 모델 상태 확인
echo "📊 현재 모델 상태:"
curl -s http://localhost:8080/api/models/status | jq '{
  current_profile: .current_profile,
  status: .status,
  gpu_memory_used: .hardware_info.gpus[0].memory_used_mb,
  gpu_memory_total: .hardware_info.gpus[0].memory_total_mb
}'

# 2. GPU 메모리 사용률 확인
GPU_USAGE=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F, '{print int($1/$2*100)}')
echo "🖥️ GPU 메모리 사용률: ${GPU_USAGE}%"

# 3. 모델 응답 시간 테스트
RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{"messages":[{"role":"user","content":"Hi"}],"model":"current","stream":false}')

echo "⚡ 모델 응답 시간: ${RESPONSE_TIME}초"

# 4. 경고 임계값 체크
if (( $(echo "$RESPONSE_TIME > 5.0" | bc -l) )); then
    echo "⚠️ 경고: 응답 시간이 느립니다 (${RESPONSE_TIME}초 > 5초)"
    ./webhook_alert.sh "WARNING" "Model response time slow: ${RESPONSE_TIME}s"
fi

if [ $GPU_USAGE -gt 95 ]; then
    echo "🔥 위험: GPU 메모리 부족 (${GPU_USAGE}%)"
    ./webhook_alert.sh "CRITICAL" "GPU memory critical: ${GPU_USAGE}%"
fi
```

#### **모델 전환 운영 절차**
```bash
#!/bin/bash  
# model_switch_procedure.sh

MODEL_ID=$1
if [ -z "$MODEL_ID" ]; then
    echo "사용법: $0 <profile_id>"
    echo "사용 가능한 모델: deepseek-r1-distill-qwen-14b, deepseek-coder-7b, qwen2-7b-instruct"
    exit 1
fi

echo "🔄 모델 전환 시작: $MODEL_ID"

# 1. 현재 상태 백업
CURRENT_STATE=$(curl -s http://localhost:8080/api/models/status)
echo "$CURRENT_STATE" > "/tmp/model_state_backup_$(date +%Y%m%d_%H%M%S).json"

# 2. 하드웨어 호환성 사전 검증
echo "🔍 하드웨어 호환성 검증 중..."
COMPATIBILITY=$(curl -s http://localhost:8080/api/models/hardware-recommendations | jq --arg model "$MODEL_ID" '.compatible_profiles[] | select(.profile_id == $model)')

if [ -z "$COMPATIBILITY" ]; then
    echo "❌ 오류: $MODEL_ID는 현재 하드웨어와 호환되지 않습니다"
    exit 1
fi

# 3. 사용자 확인
echo "✅ 호환성 확인 완료"
echo "현재 활성 사용자 수 확인 중..."
ACTIVE_USERS=$(docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(DISTINCT user_id) FROM conversations WHERE updated_at > NOW() - INTERVAL '5 minutes';" | xargs)
echo "📊 활성 사용자: $ACTIVE_USERS명"

if [ "$ACTIVE_USERS" -gt 0 ]; then
    echo "⚠️ 주의: 현재 $ACTIVE_USERS명이 서비스 사용 중입니다"
    echo "계속하시겠습니까? (y/N)"
    read -r CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "모델 전환 취소됨"
        exit 0
    fi
fi

# 4. 모델 전환 실행
echo "🚀 모델 전환 요청 전송..."
SWITCH_RESULT=$(curl -s -X POST http://localhost:8080/api/models/switch \
    -H "Content-Type: application/json" \
    -d "{\"profile_id\": \"$MODEL_ID\"}")

echo "📝 전환 응답: $SWITCH_RESULT"

# 5. 전환 완료 대기
echo "⏳ 모델 로딩 대기 중... (최대 5분)"
for i in {1..60}; do
    STATUS=$(curl -s http://localhost:8080/api/models/status | jq -r '.status')
    if [ "$STATUS" = "running" ]; then
        echo "✅ 모델 전환 완료! (${i}0초 소요)"
        break
    elif [ "$STATUS" = "error" ]; then
        echo "❌ 모델 전환 실패!"
        exit 1
    fi
    sleep 5
    echo -n "."
done

# 6. 전환 완료 검증
echo ""
echo "🧪 모델 전환 검증 중..."
TEST_RESULT=$(curl -s -X POST http://localhost:8080/api/chat \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-token" \
    -d '{"messages":[{"role":"user","content":"안녕하세요"}],"model":"current","stream":false}')

if echo "$TEST_RESULT" | jq -e '.choices[0].message.content' > /dev/null; then
    echo "✅ 모델 전환 및 테스트 완료!"
    ./webhook_alert.sh "INFO" "Model switched successfully to: $MODEL_ID"
else
    echo "❌ 모델 전환은 완료되었으나 테스트 실패"
    ./webhook_alert.sh "WARNING" "Model switch completed but test failed: $MODEL_ID"
fi
```

#### **모델 관련 트러블슈팅**

**🔥 일반적인 문제와 해결책:**

1. **모델 전환이 멈춤 (5분 이상)**
```bash
# 현재 vLLM 프로세스 확인
docker compose exec vllm ps aux | grep python

# GPU 메모리 상태 확인  
nvidia-smi

# 강제 재시작 (최후 수단)
docker compose restart vllm
sleep 30
curl http://localhost:8080/api/models/reload  # 프로파일 재로드
```

2. **GPU 메모리 부족 (CUDA OOM)**
```bash
# 현재 메모리 사용량 확인
nvidia-smi

# 더 작은 모델로 전환
curl -X POST http://localhost:8080/api/models/switch \
    -H "Content-Type: application/json" \
    -d '{"profile_id": "phi3-mini"}'

# VRAM 사용률 조정 (model_profiles.yml)
# gpu_memory_utilization: 0.85 → 0.7
```

3. **모델 응답 품질 저하**
```bash
# 현재 모델 확인
curl http://localhost:8080/api/models/status | jq '.current_profile'

# 모델별 권장 매개변수 확인
curl http://localhost:8080/api/models/profiles | jq '.profiles["current"]["description"]'

# 더 적합한 모델로 전환
curl http://localhost:8080/api/models/hardware-recommendations | jq '.recommended_profiles'
```

4. **모델 로딩 실패**
```bash
# vLLM 컨테이너 로그 확인
docker compose logs vllm | tail -50

# 하드웨어 요구사항 재확인
curl http://localhost:8080/api/models/hardware-recommendations

# model_profiles.yml 문법 검증
python3 -c "import yaml; yaml.safe_load(open('model_profiles.yml'))"
```

### 주간 유지보수 (매주 일요일)

```bash
#!/bin/bash
# weekly_maintenance.sh

echo "🔧 주간 유지보수 시작: $(date)"

# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. Docker 정리
docker system prune -f
docker volume prune -f

# 3. 로그 파일 정리 (30일 이상된 파일 삭제)
find logs/ -name "*.log" -mtime +30 -delete

# 4. 데이터베이스 진공청소
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "VACUUM ANALYZE;"

# 5. GPU 드라이버 상태 확인
nvidia-smi -q -d TEMPERATURE,POWER,CLOCK

# 6. 백업 무결성 검증
./scripts/verify_backups.sh

# 7. 성능 벤치마크 (부하가 적은 시간대)
./scripts/benchmark.sh

echo "✅ 주간 유지보수 완료: $(date)"
```

### 월간 유지보수 (매월 첫째 주)

```bash
#!/bin/bash
# monthly_maintenance.sh

echo "🔧 월간 유지보수 시작: $(date)"

# 1. 보안 업데이트
sudo apt update && sudo apt full-upgrade -y

# 2. SSL 인증서 갱신 확인
sudo certbot renew --dry-run

# 3. 데이터베이스 백업 아카이빙
tar -czf "backups/monthly_backup_$(date +%Y%m).tar.gz" backups/daily/

# 4. 로그 아카이빙
tar -czf "logs/monthly_logs_$(date +%Y%m).tar.gz" logs/daily/

# 5. 의존성 업데이트 검토
docker compose pull  # 새 이미지 확인

# 6. 보안 스캔
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image $(docker compose config --services)

echo "✅ 월간 유지보수 완료: $(date)"
```

## 💾 백업 및 복구

### 자동 백업 스크립트

```bash
#!/bin/bash
# scripts/backup_database.sh

BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/chatdb_backup_$DATE.sql"

# 디렉토리 생성
mkdir -p $BACKUP_DIR

# 데이터베이스 덤프
docker compose exec -T postgres pg_dump \
    -U ${POSTGRES_USER} \
    -d ${POSTGRES_DB} \
    --clean --if-exists \
    > $BACKUP_FILE

# 압축
gzip $BACKUP_FILE

# 30일 이상된 백업 파일 삭제
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "✅ 백업 완료: ${BACKUP_FILE}.gz"

# Slack 알림 (선택사항)
# ./webhook_alert.sh "INFO" "Database backup completed: ${BACKUP_FILE}.gz"
```

### 백업 복구 절차

```bash
#!/bin/bash
# scripts/restore_database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "사용법: ./restore_database.sh backup_file.sql.gz"
    exit 1
fi

echo "⚠️  주의: 현재 데이터베이스가 완전히 교체됩니다!"
read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "복구가 취소되었습니다."
    exit 1
fi

# 서비스 중지
docker compose stop gateway frontend

# 백업 파일 압축 해제 및 복구
gunzip -c $BACKUP_FILE | docker compose exec -T postgres psql \
    -U ${POSTGRES_USER} \
    -d ${POSTGRES_DB}

# 서비스 재시작
docker compose start gateway frontend

echo "✅ 데이터베이스 복구 완료"
```

### 설정 파일 백업

```bash
#!/bin/bash
# scripts/backup_configs.sh

BACKUP_DIR="/backups/configs"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 중요 설정 파일들 백업
tar -czf "$BACKUP_DIR/configs_backup_$DATE.tar.gz" \
    .env.local \
    docker-compose.yml \
    nginx/nginx.conf \
    gateway/app/config.py \
    scripts/

echo "✅ 설정 파일 백업 완료: configs_backup_$DATE.tar.gz"
```

## 🚨 장애 대응 매뉴얼

### 일반적인 장애 시나리오

#### 1. vLLM 서비스 다운

**증상:**

- 502 Bad Gateway 오류
- `/v1/models` 엔드포인트 응답 없음

**대응 절차:**

```bash
# 1. 로그 확인
docker compose logs vllm | tail -50

# 2. GPU 상태 확인
nvidia-smi

# 3. 컨테이너 재시작
docker compose restart vllm

# 4. 모델 로딩 대기 (5-10분)
timeout 600 bash -c 'until curl -f http://localhost:8000/v1/models; do sleep 15; done'
```

#### 2. 데이터베이스 연결 실패

**증상:**

- Gateway 에러 로그에 DB 연결 오류
- 사용자 인증 실패

**대응 절차:**

```bash
# 1. PostgreSQL 상태 확인
docker compose exec postgres pg_isready

# 2. 연결 수 확인
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
SELECT count(*) FROM pg_stat_activity;"

# 3. 필요시 PostgreSQL 재시작
docker compose restart postgres

# 4. Gateway 재시작 (연결 재설정)
docker compose restart gateway
```

#### 3. 디스크 공간 부족

**증상:**

- 로그에 "No space left on device"
- 새로운 대화 저장 실패

**대응 절차:**

```bash
# 1. 용량 확인
df -h

# 2. 큰 파일들 찾기
du -sh * | sort -hr | head -10

# 3. 임시 정리
docker system prune -f
docker logs --details > /dev/null  # 로그 버퍼 비우기

# 4. 로그 파일 압축
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
```

### 응급 연락처 및 에스컬레이션

```bash
# emergency_contacts.md
## 🚨 응급 연락처

### 1차 대응 (24시간)
- 운영 담당자: [전화번호]
- 개발 팀장: [전화번호]

### 2차 에스컬레이션 (심각한 장애)
- CTO/기술책임자: [전화번호]
- 인프라 팀: [전화번호]

### 외부 지원
- 클라우드 지원팀: [연락처]
- NVIDIA 기술지원: [연락처]

### 커뮤니케이션 채널
- Slack: #vllm-operations
- 이메일: ops@company.com
- 상황실: [회의실/화상회의 링크]
```

## 📊 성능 최적화

### GPU 성능 튜닝

```bash
# gpu_tuning.sh
#!/bin/bash

# GPU 클럭 최대화 (NVIDIA GPU)
nvidia-smi -pm ENABLED
nvidia-smi -ac 877,1911  # 메모리, GPU 클럭 설정

# GPU 파워 리밋 설정
nvidia-smi -pl 350  # 350W로 설정 (GPU 모델에 따라 조정)

# 온도 모니터링
nvidia-smi -q -d TEMPERATURE
```

### vLLM 파라미터 최적화

```bash
# 성능 테스트 기반 최적 파라미터 찾기
#!/bin/bash

MODELS=("microsoft/DialoGPT-medium" "microsoft/DialoGPT-small")
UTILS=(0.4 0.5 0.6 0.7)
MAX_LENS=(2048 4096 8192)

for MODEL in "${MODELS[@]}"; do
    for UTIL in "${UTILS[@]}"; do
        for MAX_LEN in "${MAX_LENS[@]}"; do
            echo "Testing MODEL=$MODEL UTIL=$UTIL MAX_LEN=$MAX_LEN"

            # 환경변수 업데이트
            sed -i "s/MODEL_ID=.*/MODEL_ID=$MODEL/" .env.local
            sed -i "s/VLLM_UTIL=.*/VLLM_UTIL=$UTIL/" .env.local
            sed -i "s/VLLM_MAXLEN=.*/VLLM_MAXLEN=$MAX_LEN/" .env.local

            # 서비스 재시작
            docker compose restart vllm
            sleep 300  # 모델 로딩 대기

            # 성능 테스트
            k6 run --duration 300s k6/load-test.js > "results_${MODEL##*/}_${UTIL}_${MAX_LEN}.txt"
        done
    done
done
```

### 데이터베이스 성능 최적화

```sql
-- PostgreSQL 성능 튜닝 쿼리
-- scripts/optimize_database.sql

-- 1. 인덱스 사용률 확인
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 2. 자주 사용되는 쿼리 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_created_at_desc
ON messages (created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_request_logs_user_model
ON request_logs (user_id, model, created_at);

-- 3. 테이블 통계 업데이트
ANALYZE;

-- 4. 오래된 세션 정리
DELETE FROM user_sessions WHERE expires_at < NOW() - INTERVAL '7 days';
```

## 📈 용량 계획

### 성장 예측 및 리소스 계획

```bash
# capacity_planning.sh
#!/bin/bash

# 현재 사용량 측정
echo "=== 현재 리소스 사용량 ==="
echo "GPU 메모리: $(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader)"
echo "시스템 메모리: $(free -h | grep Mem)"
echo "디스크 사용량: $(df -h /)"
echo "DB 크기: $(docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB}'));")"

# 월간 증가율 계산
echo "=== 성장 추세 분석 ==="
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
WITH monthly_stats AS (
    SELECT
        DATE_TRUNC('month', created_at) as month,
        COUNT(*) as requests,
        COUNT(DISTINCT user_id) as active_users
    FROM request_logs
    WHERE created_at >= NOW() - INTERVAL '6 months'
    GROUP BY DATE_TRUNC('month', created_at)
    ORDER BY month
)
SELECT
    month,
    requests,
    active_users,
    LAG(requests) OVER (ORDER BY month) as prev_requests,
    ROUND((requests - LAG(requests) OVER (ORDER BY month)) * 100.0 / LAG(requests) OVER (ORDER BY month), 2) as growth_rate
FROM monthly_stats;"
```

### 확장 계획

```yaml
# docker-compose.scale.yml
# 높은 부하를 위한 확장 설정

version: '3.9'
services:
  gateway:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  nginx:
    volumes:
      - ./nginx/nginx.scale.conf:/etc/nginx/nginx.conf

  postgres:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
    environment:
      - shared_preload_libraries=pg_stat_statements
      - max_connections=200
      - work_mem=16MB
```

이제 vLLM 챗봇 서비스의 완전한 운영 체계가 갖춰졌습니다! 일일 점검부터 장애 대응, 성능 최적화까지 모든 운영 상황에 대비할 수 있습니다. 🚀
