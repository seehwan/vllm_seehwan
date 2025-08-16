#!/bin/bash
set -e

echo "📊 vLLM 서비스 성능 벤치마크 시작..."

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 환경변수 로드
if [ -f .env.local ]; then
    source .env.local
else
    print_error ".env.local 파일이 없습니다."
    exit 1
fi

# 결과 디렉토리 생성
RESULT_DIR="./benchmark_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULT_DIR"

print_status "벤치마크 결과는 $RESULT_DIR 에 저장됩니다."

# 서비스 상태 확인
print_status "서비스 상태 확인 중..."

# Gateway 상태 확인
if ! curl -f http://localhost:${GATEWAY_PORT}/health > /dev/null 2>&1; then
    print_error "Gateway 서비스가 응답하지 않습니다."
    exit 1
fi

# vLLM 상태 확인
if ! curl -f http://localhost:${VLLM_PORT}/v1/models > /dev/null 2>&1; then
    print_error "vLLM 서비스가 응답하지 않습니다."
    exit 1
fi

print_success "모든 서비스가 정상 상태입니다."

# GPU 모니터링 시작
print_status "GPU 모니터링 시작..."
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv -l 5 > "$RESULT_DIR/gpu_stats.csv" &
GPU_MONITOR_PID=$!

# 시스템 리소스 모니터링 시작
print_status "시스템 리소스 모니터링 시작..."
(
    echo "timestamp,cpu_percent,memory_percent,memory_used_gb,memory_total_gb"
    while true; do
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
        MEM_INFO=$(free -g | grep Mem)
        MEM_TOTAL=$(echo $MEM_INFO | awk '{print $2}')
        MEM_USED=$(echo $MEM_INFO | awk '{print $3}')
        MEM_PERCENT=$(echo "scale=2; $MEM_USED * 100 / $MEM_TOTAL" | bc)
        echo "$TIMESTAMP,$CPU,$MEM_PERCENT,$MEM_USED,$MEM_TOTAL"
        sleep 5
    done
) > "$RESULT_DIR/system_stats.csv" &
SYS_MONITOR_PID=$!

# K6 설치 확인
if ! command -v k6 &> /dev/null; then
    print_warning "k6가 설치되지 않았습니다. 설치 중..."
    
    # K6 설치 (Ubuntu/Debian)
    sudo gpg -k
    sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
    echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
    sudo apt-get update
    sudo apt-get install -y k6
fi

# 1. 기본 부하 테스트
print_status "🔥 K6 기본 부하 테스트 실행 중..."
k6 run --out json="$RESULT_DIR/load_test_results.json" k6/load-test.js > "$RESULT_DIR/load_test_summary.txt" 2>&1
if [ $? -eq 0 ]; then
    print_success "기본 부하 테스트 완료"
else
    print_error "기본 부하 테스트 실패"
fi

# 2. 스트리밍 테스트
print_status "🌊 스트리밍 성능 테스트 실행 중..."
k6 run --out json="$RESULT_DIR/streaming_test_results.json" k6/streaming-test.js > "$RESULT_DIR/streaming_test_summary.txt" 2>&1
if [ $? -eq 0 ]; then
    print_success "스트리밍 테스트 완료"
else
    print_error "스트리밍 테스트 실패"
fi

# 3. Vegeta 처리량 테스트 (선택적)
if command -v vegeta &> /dev/null; then
    print_status "🌪️ Vegeta 처리량 테스트 실행 중..."
    
    # 테스트 페이로드 생성
    cat > "$RESULT_DIR/vegeta_payload.json" << EOF
{
  "model": "microsoft/DialoGPT-medium",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "temperature": 0.7,
  "max_tokens": 100
}
EOF

    # Vegeta 테스트 실행
    echo "POST http://localhost:${GATEWAY_PORT}/api/chat
Content-Type: application/json
Authorization: Bearer test-token
@$RESULT_DIR/vegeta_payload.json" | \
    vegeta attack -duration=60s -rate=20 > "$RESULT_DIR/vegeta_results.bin"
    
    # 결과 분석
    vegeta report < "$RESULT_DIR/vegeta_results.bin" > "$RESULT_DIR/vegeta_report.txt"
    vegeta plot < "$RESULT_DIR/vegeta_results.bin" > "$RESULT_DIR/vegeta_plot.html"
    
    print_success "Vegeta 테스트 완료"
else
    print_warning "Vegeta가 설치되지 않아 건너뜀"
fi

# 4. 단일 요청 지연 시간 테스트
print_status "⏱️ 단일 요청 지연 시간 테스트..."
LATENCY_TEST_FILE="$RESULT_DIR/latency_test.txt"
echo "Single Request Latency Test Results" > "$LATENCY_TEST_FILE"
echo "====================================" >> "$LATENCY_TEST_FILE"

for i in {1..10}; do
    START_TIME=$(date +%s%N)
    
    RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer test-token" \
        -d '{"messages":[{"role":"user","content":"Hello"}],"model":"microsoft/DialoGPT-medium","max_tokens":50}' \
        http://localhost:${GATEWAY_PORT}/api/chat)
    
    END_TIME=$(date +%s%N)
    TOTAL_TIME=$(( (END_TIME - START_TIME) / 1000000 )) # ms로 변환
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n2 | head -n1)
    CURL_TIME=$(echo "$RESPONSE" | tail -n1)
    
    echo "Request $i: HTTP $HTTP_CODE, Total Time: ${TOTAL_TIME}ms, Curl Time: ${CURL_TIME}s" >> "$LATENCY_TEST_FILE"
done

print_success "지연 시간 테스트 완료"

# 5. 동시성 테스트 (간단한 버전)
print_status "🔄 동시성 테스트 실행 중..."
CONCURRENT_TEST_FILE="$RESULT_DIR/concurrent_test.txt"
echo "Concurrent Requests Test Results" > "$CONCURRENT_TEST_FILE"
echo "=================================" >> "$CONCURRENT_TEST_FILE"

for CONCURRENT in 1 3 5 10; do
    echo "Testing with $CONCURRENT concurrent requests..." >> "$CONCURRENT_TEST_FILE"
    
    START_TIME=$(date +%s)
    
    for i in $(seq 1 $CONCURRENT); do
        (
            RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null \
                -X POST \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer test-token" \
                -d '{"messages":[{"role":"user","content":"Quick test"}],"model":"microsoft/DialoGPT-medium","max_tokens":30}' \
                http://localhost:${GATEWAY_PORT}/api/chat)
            echo "Concurrent $i: ${RESPONSE_TIME}s" >> "$RESULT_DIR/concurrent_${CONCURRENT}_details.txt"
        ) &
    done
    
    wait
    
    END_TIME=$(date +%s)
    TOTAL_DURATION=$((END_TIME - START_TIME))
    
    echo "Concurrent Level: $CONCURRENT, Total Duration: ${TOTAL_DURATION}s" >> "$CONCURRENT_TEST_FILE"
    
    # 개별 결과 요약
    if [ -f "$RESULT_DIR/concurrent_${CONCURRENT}_details.txt" ]; then
        AVG_TIME=$(awk '{sum+=$3; count++} END {print sum/count}' "$RESULT_DIR/concurrent_${CONCURRENT}_details.txt")
        echo "Average Response Time: ${AVG_TIME}s" >> "$CONCURRENT_TEST_FILE"
    fi
    
    echo "" >> "$CONCURRENT_TEST_FILE"
done

print_success "동시성 테스트 완료"

# 모니터링 중지
print_status "모니터링 중지 중..."
kill $GPU_MONITOR_PID 2>/dev/null || true
kill $SYS_MONITOR_PID 2>/dev/null || true

# 결과 요약 생성
print_status "결과 요약 생성 중..."
SUMMARY_FILE="$RESULT_DIR/benchmark_summary.md"

cat > "$SUMMARY_FILE" << EOF
# vLLM 서비스 벤치마크 결과

**실행 시간**: $(date)
**시스템**: $(uname -a)
**GPU**: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)

## 테스트 환경
- **모델**: ${MODEL_ID}
- **vLLM 설정**: TP=${VLLM_TP}, Max Length=${VLLM_MAXLEN}, GPU Util=${VLLM_UTIL}
- **Frontend**: http://localhost:${FRONTEND_PORT}
- **Gateway**: http://localhost:${GATEWAY_PORT}
- **vLLM**: http://localhost:${VLLM_PORT}

## 파일 목록
EOF

# 생성된 파일 목록 추가
ls -la "$RESULT_DIR" >> "$SUMMARY_FILE"

echo "" >> "$SUMMARY_FILE"
echo "## 빠른 결과 확인" >> "$SUMMARY_FILE"
echo "- K6 부하 테스트 요약: \`cat $RESULT_DIR/load_test_summary.txt\`" >> "$SUMMARY_FILE"
echo "- 지연 시간 테스트: \`cat $RESULT_DIR/latency_test.txt\`" >> "$SUMMARY_FILE"
echo "- GPU 사용률: \`tail -20 $RESULT_DIR/gpu_stats.csv\`" >> "$SUMMARY_FILE"

if [ -f "$RESULT_DIR/vegeta_report.txt" ]; then
    echo "- Vegeta 보고서: \`cat $RESULT_DIR/vegeta_report.txt\`" >> "$SUMMARY_FILE"
    echo "- Vegeta 플롯: $RESULT_DIR/vegeta_plot.html" >> "$SUMMARY_FILE"
fi

print_success "🎉 벤치마크 완료!"
echo ""
print_status "결과 위치: $RESULT_DIR"
print_status "요약 보고서: $SUMMARY_FILE"
echo ""
print_status "주요 결과 확인:"
print_status "  cat $RESULT_DIR/benchmark_summary.md"
print_status "  cat $RESULT_DIR/load_test_summary.txt | grep -A 10 'checks'"
print_status "  tail -10 $RESULT_DIR/gpu_stats.csv"
