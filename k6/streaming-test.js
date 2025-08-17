import http from 'k6/http'
import { check, sleep } from 'k6'
import { Rate, Trend } from 'k6/metrics'

// SSE 스트리밍 테스트용 메트릭
const streamingErrorRate = new Rate('streaming_errors')
const ttftTrend = new Trend('time_to_first_token', true)

export const options = {
  stages: [
    { duration: '1m', target: 1 }, // 단일 사용자로 시작
    { duration: '3m', target: 3 }, // 3명 동시 스트리밍
    { duration: '2m', target: 5 }, // 5명 동시 스트리밍
    { duration: '2m', target: 0 }, // 종료
  ],
  thresholds: {
    time_to_first_token: ['p(50)<2000', 'p(95)<4000'], // TTFT 목표
    streaming_errors: ['rate<0.05'], // 스트리밍 에러율 5% 미만
  },
}

export function setup() {
  // 테스트용 토큰 (실제 환경에서는 유효한 토큰 사용)
  return { token: 'test-token' }
}

export default function (data) {
  const payload = JSON.stringify({
    messages: [
      {
        role: 'user',
        content:
          'Write a detailed explanation about machine learning algorithms. Please provide examples and use cases.',
      },
    ],
    model: 'current', // 현재 활성화된 모델 사용
    temperature: 0.7,
    max_tokens: 500,
    stream: true,
  })

  const params = {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${data.token}`,
      Accept: 'text/event-stream',
      'Cache-Control': 'no-cache',
    },
    timeout: '120s',
  }

  const startTime = Date.now()
  let firstTokenReceived = false
  let ttft = 0

  const response = http.post('http://localhost:8080/api/chat', payload, params)

  // SSE 스트리밍 응답 파싱 시뮬레이션
  const isStreamingSuccess = check(response, {
    'status is 200': (r) => r.status === 200,
    'content-type is SSE': (r) =>
      r.headers['content-type'] &&
      r.headers['content-type'].includes('text/event-stream'),
    'has streaming data': (r) => r.body && r.body.includes('data: '),
  })

  if (!isStreamingSuccess) {
    streamingErrorRate.add(1)
    console.error(`Streaming Error: Status ${response.status}`)
  } else {
    streamingErrorRate.add(0)

    // 첫 번째 토큰 시간 시뮬레이션 (실제로는 SSE 파싱 필요)
    if (response.body.includes('data: ')) {
      ttft = Date.now() - startTime
      ttftTrend.add(ttft)
    }
  }

  sleep(2)
}
