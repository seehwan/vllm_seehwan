# K6 Load Testing

vLLM 챗봇 서비스의 성능 테스트를 위한 K6 스크립트 모음입니다.

## 📊 테스트 스크립트

### load-test.js

**기본 부하 테스트**

전체적인 API 성능과 안정성을 측정하는 메인 테스트입니다.

**테스트 시나리오:**

- 워밍업: 1명 사용자 (2분)
- 정상 부하: 5명 동시 사용자 (5분)
- 피크 테스트: 10명 동시 사용자 (2분)
- 스트레스 테스트: 15명 동시 사용자 (1분)

**성능 목표:**

- p50 응답시간 < 1.5초
- p95 응답시간 < 3초
- p99 응답시간 < 5초
- 에러율 < 1%

### streaming-test.js

**스트리밍 성능 테스트**

SSE(Server-Sent Events) 스트리밍 기능의 성능을 검증합니다.

**측정 항목:**

- TTFT (Time To First Token) < 2초
- 스트리밍 에러율 < 5%
- 연결 안정성 검증
- 토큰 처리 성능

## 🚀 테스트 실행

### 필수 요구사항

```bash
# K6 설치 (Ubuntu/Debian)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

### 개별 테스트 실행

```bash
# 기본 부하 테스트
k6 run k6/load-test.js

# 스트리밍 테스트
k6 run k6/streaming-test.js

# 결과를 JSON으로 저장
k6 run --out json=results.json k6/load-test.js

# 실시간 결과 모니터링
k6 run --out influxdb=http://localhost:8086/k6 k6/load-test.js
```

### 자동화된 벤치마크

```bash
# 전체 벤치마크 실행 (scripts/benchmark.sh 사용)
./scripts/benchmark.sh
```

## ⚙️ 테스트 설정

### 환경변수

```bash
# API 엔드포인트 설정
export API_BASE_URL=http://localhost:8080
export API_TOKEN=your-test-token

# 테스트 사용자 인증 정보
export TEST_EMAIL=test@example.com
export TEST_PASSWORD=test123
```

### 커스텀 설정

#### 부하 프로필 수정

```javascript
// load-test.js에서 스테이지 조정
export const options = {
  stages: [
    { duration: '1m', target: 1 }, // 더 짧은 워밍업
    { duration: '10m', target: 10 }, // 더 긴 테스트
    { duration: '2m', target: 20 }, // 더 높은 부하
    { duration: '3m', target: 0 },
  ],
}
```

#### 임계값 조정

```javascript
// 더 엄격한 성능 기준
thresholds: {
  http_req_duration: ['p(50)<1000', 'p(95)<2000'], // 더 빠른 응답시간 요구
  http_req_failed: ['rate<0.005'], // 0.5% 미만 에러율
  checks: ['rate>0.95'], // 95% 이상 성공률
}
```

## 📈 결과 분석

### 핵심 메트릭

#### 응답 시간 (Response Time)

- **p50 (median)**: 50%의 요청이 이 시간 내에 완료
- **p95**: 95%의 요청이 이 시간 내에 완료
- **p99**: 99%의 요청이 이 시간 내에 완료

#### 처리량 (Throughput)

- **RPS (Requests Per Second)**: 초당 처리 요청 수
- **데이터 전송량**: 송수신 바이트 수

#### 에러율 (Error Rate)

- **HTTP 4xx/5xx 응답률**
- **연결 실패율**
- **타임아웃 발생률**

### 결과 해석

#### 좋은 성능 지표

```
✓ http_req_duration..............: avg=1.2s min=0.8s med=1.1s max=3.2s p(90)=1.8s p(95)=2.4s
✓ http_req_failed................: 0.12%   ✓ 247 ✗ 3
✓ http_reqs......................: 250     20.83/s
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

# 커스텀 보고서 스크립트
python3 scripts/generate_report.py results.json > performance_report.html
```

### 보고서 템플릿

```markdown
# 성능 테스트 보고서

## 테스트 환경

- 날짜: 2025-01-XX
- 모델: microsoft/DialoGPT-medium
- vLLM 설정: TP=2, Util=0.55

## 결과 요약

- 평균 응답시간: X.XX초
- 처리량: XX.X RPS
- 에러율: X.XX%

## 권장사항

- [...개선 사항...]
```

K6 테스트 도구를 활용하여 체계적인 성능 검증과 최적화가 가능해졌습니다!
