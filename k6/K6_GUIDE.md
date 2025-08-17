# 🚀 K6 성능 테스트 가이드

vLLM 챗봇 서비스의 성능 테스트를 위한 K6 스크립트 모음입니다.

## 📊 테스트 스크립트 개요

### 🎯 Core Performance Tests

#### **load-test.js** - 기본 부하 테스트
- **목적**: 전체적인 API 성능과 안정성 측정  
- **시나리오**: 1→5→10→15명 단계적 부하 증가
- **측정**: 응답시간, 에러율, 처리량
- **실행 시간**: ~13분

#### **streaming-test.js** - 스트리밍 성능 테스트  
- **목적**: SSE(Server-Sent Events) 스트리밍 기능 검증
- **시나리오**: 1→3→5명 동시 스트리밍 연결
- **측정**: TTFT(Time To First Token), 스트리밍 안정성
- **실행 시간**: ~8분

#### **comprehensive-test.js** - 종합 성능 테스트 🆕
- **목적**: 다중 시나리오 동시 실행으로 실제 사용 패턴 시뮬레이션
- **시나리오**: 채팅 부하 + 스트리밍 + API 안정성 병렬 테스트
- **측정**: 종합 성능 메트릭 및 리소스 사용률
- **실행 시간**: ~10분

#### **model-management-test.js** - 모델 관리 API 테스트 🆕
- **목적**: 모델 전환 성능 및 관리 API 안정성 검증
- **시나리오**: 자동 모델 전환, API 호출, 상태 모니터링
- **측정**: 모델 전환 시간, API 응답성, 전환 성공률  
- **실행 시간**: ~10분

## 🎯 성능 목표 (Performance SLA)

### **응답 시간 (Response Time)**
- 🎯 **TTFT (Time To First Token)**: < 2초
- 🎯 **일반 채팅**: p50 < 1.5초, p95 < 3초, p99 < 5초
- 🎯 **복잡한 질문**: p50 < 3초, p95 < 8초
- 🎯 **API 호출**: p95 < 5초

### **안정성 (Reliability)**
- 🎯 **에러율**: < 1% (일반), < 5% (스트리밍)
- 🎯 **가용성**: > 99.5%
- 🎯 **모델 전환 성공률**: > 90%

### **처리량 (Throughput)**  
- 🎯 **동시 사용자**: 10명 이상 지원
- 🎯 **RPS (Requests Per Second)**: 20+ 
- 🎯 **토큰 처리**: 1000+ tokens/min

## � 설치 및 실행

### **K6 설치**

```bash
# Linux (Ubuntu/Debian) - APT 패키지
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Linux - 직접 바이너리 다운로드 (권장)
wget https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz
tar -xzf k6-v0.47.0-linux-amd64.tar.gz
sudo mv k6-v0.47.0-linux-amd64/k6 /usr/local/bin/
k6 version

# macOS (Homebrew)
brew install k6

# Windows (Chocolatey)  
choco install k6

# 또는 Docker로 실행
docker pull grafana/k6:latest
```

### 🚀 **테스트 실행**

#### **개별 테스트**
```bash
# 기본 부하 테스트 (13분 소요)
k6 run load-test.js

# 스트리밍 성능 테스트 (8분 소요)
k6 run streaming-test.js

# 종합 성능 테스트 (10분 소요) 🆕
k6 run comprehensive-test.js

# 모델 관리 API 테스트 (10분 소요) 🆕
k6 run model-management-test.js

# 결과를 JSON으로 저장
k6 run --out json=results.json load-test.js

# CSV 형식으로 결과 저장  
k6 run --out csv=results.csv load-test.js
```

#### **Docker 실행** 
```bash
# 볼륨 마운트로 테스트 실행
docker run --rm -v $(pwd):/scripts grafana/k6:latest run /scripts/load-test.js

# 네트워크 연결 (서비스와 같은 네트워크)
docker run --network=host --rm -v $(pwd):/scripts grafana/k6:latest run /scripts/load-test.js
```

#### **설정 변수 (Environment Variables)**
```bash
# 기본 설정
export BASE_URL="http://localhost:8000"  # Gateway 서버 주소
export TEST_DURATION="5m"                # 테스트 지속 시간
export MAX_VUS=10                        # 최대 가상 사용자 수
export ERROR_THRESHOLD=0.01              # 에러율 임계값 (1%)

# 커스텀 설정으로 실행
k6 run -e BASE_URL=https://production.example.com load-test.js
```

### 🔄 **자동화된 테스트 실행**

```bash
# 전체 성능 테스트 실행 (scripts/benchmark.sh 사용)
./scripts/benchmark.sh

# 모든 K6 테스트를 순차적으로 실행하는 스크립트
#!/bin/bash
echo "🚀 Starting comprehensive K6 performance tests..."

# 1. 기본 부하 테스트
echo "📊 Running load test..."
k6 run --out json=results/load-test-$(date +%Y%m%d_%H%M%S).json load-test.js

# 2. 스트리밍 테스트
echo "🌊 Running streaming test..."
k6 run --out json=results/streaming-test-$(date +%Y%m%d_%H%M%S).json streaming-test.js

# 3. 종합 테스트
echo "🎯 Running comprehensive test..."  
k6 run --out json=results/comprehensive-test-$(date +%Y%m%d_%H%M%S).json comprehensive-test.js

# 4. 모델 관리 테스트
echo "🔧 Running model management test..."
k6 run --out json=results/model-management-test-$(date +%Y%m%d_%H%M%S).json model-management-test.js

echo "✅ All tests completed! Check results/ directory for detailed reports."
```

## ⚙️ **테스트 설정 및 커스터마이징**

### **환경변수 설정**

```bash
# Gateway API 설정
export API_BASE_URL="http://localhost:8000"
export API_TOKEN="your-test-token"

# 인증 정보 (필요시)
export TEST_EMAIL="test@example.com"
export TEST_PASSWORD="test123"

# 성능 임계값 설정
export RESPONSE_TIME_P95=3000    # 95퍼센타일 응답시간 (ms)
export ERROR_RATE_THRESHOLD=0.01 # 에러율 임계값 (1%)
export TTFT_THRESHOLD=2000       # TTFT 임계값 (ms)
```

### **부하 프로필 커스터마이징**

#### **load-test.js 스테이지 조정**
```javascript
export const options = {
  stages: [
    { duration: '2m', target: 2 },    // 워밍업: 2명 → 가벼운 부하
    { duration: '5m', target: 8 },    // 정상 부하: 8명 
    { duration: '3m', target: 12 },   // 피크: 12명
    { duration: '1m', target: 20 },   // 스트레스: 20명 (높은 부하)
    { duration: '2m', target: 0 },    // 종료: 0명
  ],
  thresholds: {
    http_req_duration: ['p(50)<1500', 'p(95)<3000', 'p(99)<5000'],
    http_req_failed: ['rate<0.01'], // 에러율 1% 미만
    'custom_ttft': ['p(95)<2000'],  // TTFT 95% < 2초
  }
};
```

#### **streaming-test.js 동시 연결 수 조정**
```javascript
export const options = {
  stages: [
    { duration: '1m', target: 2 },   # 스트리밍 연결 2개
    { duration: '4m', target: 5 },   # 스트리밍 연결 5개  
    { duration: '2m', target: 8 },   # 스트리밍 연결 8개 (높음)
    { duration: '1m', target: 0 },
  ]
};
```
## 📈 **결과 분석 및 성능 해석**

### 🎯 **핵심 메트릭 (Key Performance Indicators)**

#### **응답 시간 (Response Time)**
- **p50 (median)**: 50%의 요청이 이 시간 내에 완료 (일반적인 사용자 경험)
- **p95**: 95%의 요청이 이 시간 내에 완료 (대부분 사용자의 최악 경험)  
- **p99**: 99%의 요청이 이 시간 내에 완료 (극소수 사용자의 경험)
- **max**: 최대 응답 시간 (시스템 한계점)

#### **처리량 (Throughput)**
- **RPS (Requests Per Second)**: 초당 처리 요청 수 → 시스템 용량 지표
- **데이터 전송량**: 송수신 바이트 수 → 네트워크 부하 확인
- **토큰 생성률**: 초당 생성되는 토큰 수 → LLM 성능 지표

#### **안정성 (Reliability)**  
- **HTTP 에러율**: 4xx/5xx 응답률 → API 안정성
- **연결 실패율**: 네트워크/서버 연결 실패 → 인프라 안정성
- **타임아웃율**: 요청 시간 초과 → 시스템 부하 상태

### ✅ **좋은 성능 지표 예시**

```bash
✓ http_req_duration..............: avg=1.2s min=0.8s med=1.1s max=3.2s p(90)=1.8s p(95)=2.4s
✓ http_req_failed................: 0.12%   ✓ 2497 ✗ 3  
✓ http_reqs......................: 2500    25.83/s
✓ custom_ttft....................: avg=1.1s p(95)=1.8s  
✓ iterations.....................: 2500    25.83/s
✓ vus............................: 1       min=1       max=10
✓ vus_max........................: 10      min=10      max=10

# 👍 해석: 
# - 평균 응답시간 1.2초 (목표 < 1.5초 달성)
# - 95% 사용자가 2.4초 내 응답 받음 (목표 < 3초 달성)
# - 에러율 0.12% (목표 < 1% 달성)  
# - TTFT 평균 1.1초 (목표 < 2초 달성)
# - 처리량 25.83 RPS (충분한 처리 능력)
```

### ⚠️ **문제가 있는 성능 지표 예시**

```bash
✗ http_req_duration..............: avg=4.5s min=1.2s med=3.8s max=15.2s p(90)=8.1s p(95)=12.4s  
✗ http_req_failed................: 5.24%   ✓ 1524 ✗ 84
✗ http_reqs......................: 1608    8.2/s
✗ custom_ttft....................: avg=5.2s p(95)=12.1s
⚠ iterations.....................: 1608    8.2/s (expected: >20/s)

# 🚨 문제점 분석:
# - 평균 응답시간 4.5초 (목표 1.5초 대비 300% 초과) 
# - 95% 응답시간 12.4초 (목표 3초 대비 400% 초과)
# - 에러율 5.24% (목표 1% 대비 5배 초과)
# - TTFT 5.2초 (목표 2초 대비 260% 초과)  
# - 처리량 8.2 RPS (목표 20+ RPS 미달)

# 🔧 개선 방안:
# 1. GPU 메모리 부족 → 모델 크기 최적화 또는 GPU 업그레이드
# 2. CPU 병목 → 워커 프로세스 수 증가 또는 CPU 업그레이드  
# 3. 네트워크 지연 → 로드밸런서/CDN 설정 확인
# 4. 데이터베이스 성능 → 쿼리 최적화 또는 커넥션 풀 튜닝
```
✓ checks.........................: 99.2%   ✓ 248 ✗ 2
```

#### 성능 문제 지표

```
✗ http_req_duration..............: avg=5.2s min=2.1s med=4.8s max=15.3s p(90)=8.9s p(95)=12.1s
✗ http_req_failed................: 8.4%    ✓ 229 ✗ 21
✗ http_reqs......................: 250     12.5/s
✗ checks.........................: 85.6%   ✓ 214 ✗ 36
```

## 🔧 테스트 시나리오 확장

### 새 테스트 케이스 추가

#### 1. 메모리 스트레스 테스트

```javascript
// memory-stress-test.js
export const options = {
  scenarios: {
    memory_stress: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '5m', target: 50 }, // 대량 동시 요청
      ],
    },
  },
}

export default function () {
  // 큰 컨텍스트를 가진 요청
  const largePrompt = 'very long prompt...'.repeat(100)
  // 테스트 로직
}
```

#### 2. 다양한 모델 테스트

```javascript
// multi-model-test.js
const models = [
  'microsoft/DialoGPT-medium',
  'microsoft/DialoGPT-large',
  // 기타 모델들
]

export default function () {
  const randomModel = models[Math.floor(Math.random() * models.length)]
  const payload = {
    model: randomModel,
    messages: [
      /*...*/
    ],
  }
  // 테스트 실행
}
```

#### 3. 인증 플로우 테스트

```javascript
// auth-flow-test.js
export function setup() {
  // 로그인하여 토큰 획득
  const loginResponse = http.post('/api/auth/login', {
    email: 'test@example.com',
    password: 'test123',
  })

  return { token: loginResponse.json('access_token') }
}

export default function (data) {
  // 인증된 요청 수행
  const headers = {
    Authorization: `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  }
  // 테스트 로직
}
```

## 📊 실시간 모니터링

### Grafana 대시보드 연동

```bash
# InfluxDB로 결과 전송
k6 run --out influxdb=http://influxdb:8086/k6db k6/load-test.js

# Grafana에서 실시간 모니터링 가능
```

### 커스텀 메트릭

```javascript
import { Trend, Counter } from 'k6/metrics'

// 사용자 정의 메트릭
const waitingTime = new Trend('waiting_time', true)
const errors = new Counter('custom_errors')

export default function () {
  const start = new Date()

  const response = http.post(/* ... */)

  const end = new Date()
  waitingTime.add(end - start)

  if (response.status >= 400) {
    errors.add(1)
  }
}
```

## 🎯 성능 최적화 가이드

### 테스트 기반 튜닝

#### 1. vLLM 파라미터 조정

```bash
# GPU 메모리 사용률 조정
VLLM_UTIL=0.6  # 0.4에서 0.6으로 증가

# 최대 시퀀스 수 조정
--max-num-seqs 128  # 기본값에서 증가

# 컨텍스트 길이 조정
--max-model-len 4096  # 메모리 상황에 따라 조정
```

#### 2. Gateway 최적화

```python
# FastAPI 워커 수 증가
uvicorn app.main:app --workers 4

# 데이터베이스 커넥션 풀 조정
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=30
```

#### 3. 시스템 리소스 최적화

```bash
# Docker 리소스 제한 조정
services:
  gateway:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### A/B 테스트

```javascript
// A/B 테스트 예시
export const options = {
  scenarios: {
    scenario_a: {
      executor: 'constant-vus',
      vus: 10,
      duration: '5m',
      tags: { test_type: 'A' },
      env: { MODEL: 'model-a' },
    },
    scenario_b: {
      executor: 'constant-vus',
      vus: 10,
      duration: '5m',
      tags: { test_type: 'B' },
      env: { MODEL: 'model-b' },
    },
  },
}
```

## 🐛 트러블슈팅

### 일반적인 문제

#### 1. 연결 거부 오류

```bash
# 서비스 상태 확인
docker compose ps
curl -f http://localhost:8080/health
```

#### 2. 메모리 부족 오류

```javascript
// 테스트 부하 감소
export const options = {
  vus: 5, // 10에서 5로 감소
  duration: '2m', // 5분에서 2분으로 감소
}
```

#### 3. 타임아웃 에러

```javascript
// 타임아웃 시간 증가
const params = {
  timeout: '300s', // 기본 60s에서 300s로 증가
}
```

### 성능 이슈 진단

#### 병목 지점 식별

```bash
# 각 컴포넌트별 응답 시간 측정
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8080/api/chat

# curl-format.txt 내용:
#     time_namelookup:  %{time_namelookup}\n
#        time_connect:  %{time_connect}\n
#     time_appconnect:  %{time_appconnect}\n
#    time_pretransfer:  %{time_pretransfer}\n
#       time_redirect:  %{time_redirect}\n
#  time_starttransfer:  %{time_starttransfer}\n
#                     ----------\n
#          time_total:  %{time_total}\n
```

## 📝 테스트 보고서 작성

### 자동 보고서 생성

```bash
# K6 결과를 HTML 보고서로 변환
k6 run --out json=results.json k6/load-test.js
cat results.json | jq '.' > formatted_results.json

### 📝 **테스트 보고서 및 결과 관리**

#### **자동 보고서 생성**

```bash
# K6 결과를 JSON으로 저장하고 HTML 보고서 생성  
k6 run --out json=results/load-test-$(date +%Y%m%d_%H%M%S).json load-test.js

# JSON 결과 포맷팅
cat results.json | jq '.' > formatted_results.json

# 커스텀 보고서 생성 (Python 스크립트 활용)
python3 scripts/generate_report.py results.json > performance_report.html
```

#### **성능 보고서 템플릿**

```markdown
# 🚀 vLLM 챗봇 성능 테스트 보고서

## 📊 테스트 환경 정보
- **실행 날짜**: 2025-01-XX  
- **모델**: microsoft/DialoGPT-medium
- **vLLM 설정**: TP=2, GPU 사용률=0.55, 최대 시퀀스=64
- **시스템**: Ubuntu 20.04, NVIDIA RTX 4090, 32GB RAM

## 📈 성능 결과 요약  
### ✅ 목표 달성 항목
- **응답시간 p95**: 2.1초 (목표: <3초) ✅
- **TTFT p95**: 1.7초 (목표: <2초) ✅  
- **에러율**: 0.3% (목표: <1%) ✅
- **처리량**: 22.5 RPS (목표: >20 RPS) ✅

### ⚠️ 개선 필요 항목
- **최대 응답시간**: 12.3초 (목표: <10초) ❌
- **메모리 사용률**: 89% (목표: <80%) ⚠️

## 🔧 권장 최적화 방안
1. **GPU 메모리 최적화**: VLLM_UTIL=0.6 → 0.45로 감소
2. **워커 프로세스 증설**: 현재 2개 → 4개로 확장
3. **모델 양자화**: FP16 → INT8 고려
```

## 🚨 **트러블슈팅 가이드**

### 🔧 **일반적인 문제와 해결책**

#### **1. 연결 거부 오류 (Connection Refused)**
```bash
# 문제 진단
docker compose ps                    # 컨테이너 상태 확인  
curl -f http://localhost:8000/health # 헬스체크 실행
netstat -tulpn | grep :8000         # 포트 사용 상태 확인

# 해결 방안
docker compose up -d gateway        # Gateway 서비스 재시작
docker compose logs gateway         # 로그 확인
```

#### **2. GPU 메모리 부족 (OOM) 오류**
```bash
# 메모리 사용률 확인
nvidia-smi  

# vLLM 설정 조정 (docker-compose.yml)
environment:
  VLLM_GPU_MEMORY_UTILIZATION: "0.4"   # 0.6에서 0.4로 감소
  VLLM_MAX_NUM_SEQS: "32"              # 64에서 32로 감소

# K6 테스트 부하 감소
export MAX_VUS=5                      # 15에서 5로 감소  
export TEST_DURATION="2m"             # 5m에서 2m으로 단축
```

#### **3. 응답 시간 초과 (Timeout) 오류**  
```javascript
// k6 스크립트에서 타임아웃 시간 연장
export const options = {
  timeout: '300s',  # 기본 60s에서 300s로 증가
  
  // 또는 임계값 완화
  thresholds: {
    http_req_duration: ['p(95)<10000'], // 3000에서 10000으로 완화
  }
};
```

#### **4. 스트리밍 연결 불안정**
```javascript
// streaming-test.js에서 체크 로직 완화  
if (line.startsWith('data: ')) {
  // 타임아웃 허용치 증가
  const timeout = setTimeout(() => {
    console.warn('Stream timeout - closing connection');
    eventSource.close();
  }, 30000); // 15초에서 30초로 연장
}
```

### 🔍 **성능 병목 진단 방법**

#### **컴포넌트별 응답시간 측정**
```bash
# curl을 이용한 세부 타이밍 측정  
curl -w "@curl-format.txt" -s -o /dev/null -X POST \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"model":"current"}' \
  http://localhost:8000/api/chat

# curl-format.txt 파일 내용:
cat > curl-format.txt << EOF
    DNS lookup time:  %{time_namelookup}s
       Connect time:  %{time_connect}s
    Pretransfer time: %{time_pretransfer}s  
       Redirect time: %{time_redirect}s
  Start transfer time: %{time_starttransfer}s
                     ----------
          Total time: %{time_total}s
EOF
```

#### **시스템 리소스 모니터링**
```bash
# 실시간 리소스 사용률 모니터링
htop                    # CPU/메모리 사용률
nvidia-smi -l 1         # GPU 사용률 (1초 간격)  
iostat -x 1             # 디스크 I/O
netstat -i              # 네트워크 트래픽

# Docker 컨테이너별 리소스 사용률
docker stats --no-stream
```

---

## 🎯 **다음 단계: 성능 최적화**

### **성능 테스트 완료 후 권장 작업**
1. **📊 결과 분석**: 테스트 결과를 바탕으로 병목점 식별
2. **🔧 설정 최적화**: vLLM, Gateway, 인프라 파라미터 튜닝  
3. **📈 재테스트**: 최적화 후 성능 개선 효과 측정
4. **📝 문서화**: 최적 설정값과 성능 벤치마크 기록
5. **🔄 지속적 모니터링**: 프로덕션 환경 성능 추적 시스템 구축

### **추가 성능 테스트 시나리오**
- **🎯 부분 부하 테스트**: 특정 API 엔드포인트별 성능 측정
- **📱 모바일 시뮬레이션**: 저속 네트워크 환경 테스트
- **🌐 지역별 테스트**: 다양한 지리적 위치에서 레이턴시 측정
- **📊 장시간 안정성**: 24시간 연속 운영 안정성 테스트

---

### 📚 **관련 문서**
- [TESTING_GUIDE.md](../TESTING_GUIDE.md) - 전체 테스트 전략
- [OPERATIONS.md](../OPERATIONS.md) - 운영 및 모니터링 가이드  
- [scripts/benchmark.sh](../scripts/benchmark.sh) - 자동화된 벤치마크 실행
- [Gateway API 문서](../gateway/GATEWAY_GUIDE.md) - API 상세 명세

- 평균 응답시간: X.XX초
- 처리량: XX.X RPS
- 에러율: X.XX%

## 권장사항

- [...개선 사항...]
```

K6 테스트 도구를 활용하여 체계적인 성능 검증과 최적화가 가능해졌습니다!
