import http from 'k6/http'
import { check, sleep } from 'k6'
import { Rate, Trend } from 'k6/metrics'

// 커스텀 메트릭
const errorRate = new Rate('errors')
const responseTimeTrend = new Trend('response_time', true)

export const options = {
  stages: [
    { duration: '2m', target: 1 }, // 워밍업: 1 사용자
    { duration: '5m', target: 5 }, // 정상 부하: 5 사용자
    { duration: '2m', target: 10 }, // 피크 테스트: 10 사용자
    { duration: '1m', target: 15 }, // 스트레스 테스트: 15 사용자
    { duration: '3m', target: 0 }, // 종료
  ],
  thresholds: {
    // TTFT(Time To First Token) 목표
    http_req_duration: ['p(50)<1500', 'p(95)<3000', 'p(99)<5000'],
    // 에러율 목표
    http_req_failed: ['rate<0.01'], // 1% 미만
    errors: ['rate<0.01'],
    // 응답 시간 분포
    response_time: ['p(50)<1500', 'p(95)<3000'],
  },
}

// 테스트 데이터
const testPrompts = [
  'Hello, how are you today?',
  'Explain quantum computing in simple terms.',
  'Write a short poem about artificial intelligence.',
  'What are the benefits of renewable energy?',
  'Describe the process of photosynthesis.',
  'How does machine learning work?',
  'What is the meaning of life?',
  'Explain the concept of blockchain technology.',
  'Write a brief story about a robot and a human becoming friends.',
  'What are the main challenges facing climate change?',
]

const models = [
  'current', // 현재 활성화된 모델 사용
  // 'deepseek-r1-distill-qwen-14b', // 특정 모델 지정 시
  // 'deepseek-coder-7b',
  // 'phi3-mini',
]

export function setup() {
  // 테스트 사용자 토큰 생성 (실제 환경에서는 유효한 토큰 사용)
  const loginPayload = JSON.stringify({
    email: 'test@example.com',
    password: 'test123',
  })

  const loginParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  }

  const loginRes = http.post(
    'http://localhost:8080/api/auth/login',
    loginPayload,
    loginParams
  )

  let token = 'test-token' // 기본 토큰
  if (loginRes.status === 200) {
    const loginData = JSON.parse(loginRes.body)
    token = loginData.access_token
  }

  return { token }
}

export default function (data) {
  // 랜덤 프롬프트 선택
  const prompt = testPrompts[Math.floor(Math.random() * testPrompts.length)]
  const model = models[Math.floor(Math.random() * models.length)]

  const payload = JSON.stringify({
    messages: [
      {
        role: 'user',
        content: prompt,
      },
    ],
    model: model,
    temperature: 0.7,
    max_tokens: 150,
    stream: false, // 부하 테스트를 위해 스트리밍 비활성화
  })

  const params = {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${data.token}`,
    },
    timeout: '60s',
  }

  const startTime = Date.now()
  const response = http.post('http://localhost:8080/api/chat', payload, params)
  const endTime = Date.now()

  // 응답 시간 기록
  const responseTime = endTime - startTime
  responseTimeTrend.add(responseTime)

  // 응답 검증
  const isError = !check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 10s': (r) => r.timings.duration < 10000,
    'has response body': (r) => r.body && r.body.length > 0,
    'is valid JSON': (r) => {
      try {
        JSON.parse(r.body)
        return true
      } catch (e) {
        return false
      }
    },
  })

  if (isError) {
    errorRate.add(1)
    console.error(`Error: Status ${response.status}, Body: ${response.body}`)
  } else {
    errorRate.add(0)
  }

  // 요청 간 대기 시간 (1-3초 랜덤)
  sleep(Math.random() * 2 + 1)
}

export function teardown(data) {
  console.log('테스트 완료')
}
