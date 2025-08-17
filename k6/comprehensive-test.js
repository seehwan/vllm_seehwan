import http from 'k6/http'
import { check, sleep } from 'k6'
import { Rate, Trend, Counter } from 'k6/metrics'

// 종합 성능 메트릭
const errorRate = new Rate('errors')
const chatResponseTime = new Trend('chat_response_time', true)
const tokenThroughput = new Counter('tokens_generated')
const apiCallCounter = new Counter('api_calls')

export const options = {
  scenarios: {
    // 시나리오 1: 기본 채팅 부하 테스트
    chat_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 2 },  // 워밍업
        { duration: '3m', target: 5 },  // 정상 부하
        { duration: '2m', target: 8 },  // 피크 부하
        { duration: '1m', target: 0 },  // 종료
      ],
      exec: 'chatLoadTest',
    },
    
    // 시나리오 2: 스트리밍 성능 테스트
    streaming_test: {
      executor: 'constant-vus',
      vus: 2,
      duration: '5m',
      exec: 'streamingTest',
    },
    
    // 시나리오 3: API 안정성 테스트
    api_stability: {
      executor: 'per-vu-iterations',
      vus: 1,
      iterations: 10,
      maxDuration: '10m',
      exec: 'apiStabilityTest',
    },
  },
  
  thresholds: {
    // 전체 성능 목표
    http_req_duration: ['p(50)<2000', 'p(95)<5000', 'p(99)<10000'],
    http_req_failed: ['rate<0.05'], // 5% 미만
    errors: ['rate<0.05'],
    
    // 채팅 특화 메트릭
    chat_response_time: ['p(50)<3000', 'p(95)<8000'],
    
    // 처리량 목표 (분당 최소 요청 수)
    api_calls: ['count>=100'],
  },
}

// 다양한 테스트 시나리오별 프롬프트
const prompts = {
  simple: [
    '안녕하세요!',
    'How are you?', 
    '오늘 날씨는 어때요?',
    'Thank you!',
  ],
  
  medium: [
    'Python으로 간단한 웹 크롤러를 만드는 방법을 알려주세요.',
    'Explain the difference between machine learning and deep learning.',
    '블록체인 기술의 장단점을 설명해주세요.',
    'What are the best practices for REST API design?',
  ],
  
  complex: [
    'Write a comprehensive guide on implementing microservices architecture with Docker and Kubernetes, including best practices for monitoring and scaling.',
    'Create a detailed comparison of different database types (relational, document, graph, time-series) and explain when to use each one.',
    '대규모 분산 시스템에서 데이터 일관성을 보장하는 방법들을 비교 분석하고, CAP 정리와 함께 설명해주세요.',
  ],
}

export function setup() {
  console.log('🚀 종합 성능 테스트 시작')
  
  // 테스트 환경 검증
  const healthCheck = http.get('http://localhost:8080/health')
  if (healthCheck.status !== 200) {
    throw new Error('Gateway 서비스가 준비되지 않았습니다.')
  }
  
  const modelStatus = http.get('http://localhost:8080/api/models/status')
  if (modelStatus.status !== 200) {
    throw new Error('모델 관리 서비스가 준비되지 않았습니다.')
  }
  
  const status = JSON.parse(modelStatus.body)
  console.log(`테스트 모델: ${status.current_profile}`)
  console.log(`GPU 상태: ${JSON.stringify(status.hardware_info?.gpus?.[0] || {}, null, 2)}`)
  
  return { 
    testToken: 'test-token',
    initialModel: status.current_profile,
  }
}

// 시나리오 1: 채팅 부하 테스트
export function chatLoadTest(data) {
  apiCallCounter.add(1)
  
  // 프롬프트 복잡도별 랜덤 선택
  let selectedPrompt
  const complexity = Math.random()
  
  if (complexity < 0.4) {
    // 40%: 간단한 질문
    selectedPrompt = prompts.simple[Math.floor(Math.random() * prompts.simple.length)]
  } else if (complexity < 0.8) {
    // 40%: 중간 복잡도
    selectedPrompt = prompts.medium[Math.floor(Math.random() * prompts.medium.length)]
  } else {
    // 20%: 복잡한 질문
    selectedPrompt = prompts.complex[Math.floor(Math.random() * prompts.complex.length)]
  }

  const payload = JSON.stringify({
    messages: [{ role: 'user', content: selectedPrompt }],
    model: 'current',
    temperature: 0.7,
    max_tokens: complexity > 0.8 ? 500 : 200, // 복잡한 질문일 때 더 긴 응답
    stream: false,
  })

  const startTime = Date.now()
  const response = http.post('http://localhost:8080/api/chat', payload, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${data.testToken}`,
    },
    timeout: '60s',
  })
  
  const responseTime = Date.now() - startTime
  chatResponseTime.add(responseTime)

  const success = check(response, {
    'chat status 200': (r) => r.status === 200,
    'has valid response': (r) => {
      try {
        const body = JSON.parse(r.body)
        return body.choices && body.choices[0] && body.choices[0].message
      } catch (e) {
        return false
      }
    },
    'response time acceptable': () => responseTime < 30000, // 30초 이내
  })

  if (!success) {
    errorRate.add(1)
    console.error(`채팅 요청 실패: ${response.status} - ${response.body?.substring(0, 100)}`)
  } else {
    errorRate.add(0)
    
    // 토큰 수 추정 (실제로는 응답에서 파싱해야 함)
    try {
      const body = JSON.parse(response.body)
      if (body.usage && body.usage.completion_tokens) {
        tokenThroughput.add(body.usage.completion_tokens)
      }
    } catch (e) {
      // 토큰 수를 추정할 수 없는 경우 무시
    }
  }

  sleep(Math.random() * 2 + 1) // 1-3초 대기
}

// 시나리오 2: 스트리밍 테스트
export function streamingTest(data) {
  apiCallCounter.add(1)
  
  const payload = JSON.stringify({
    messages: [{ 
      role: 'user', 
      content: '인공지능의 미래와 현재 기술 동향에 대해 상세히 설명해주세요. 구체적인 예시와 함께 장단점을 포함해서 답변해주세요.'
    }],
    model: 'current',
    temperature: 0.8,
    max_tokens: 400,
    stream: true,
  })

  const response = http.post('http://localhost:8080/api/chat', payload, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${data.testToken}`,
      'Accept': 'text/event-stream',
    },
    timeout: '90s',
  })

  const streamingSuccess = check(response, {
    'streaming status 200': (r) => r.status === 200,
    'streaming content type': (r) => r.headers['content-type']?.includes('event-stream') || r.body?.includes('data:'),
    'has streaming data': (r) => r.body && r.body.length > 0,
  })

  if (!streamingSuccess) {
    errorRate.add(1)
    console.error(`스트리밍 실패: ${response.status}`)
  } else {
    errorRate.add(0)
  }

  sleep(3) // 스트리밍은 더 긴 간격
}

// 시나리오 3: API 안정성 테스트
export function apiStabilityTest(data) {
  const apis = [
    { url: '/health', method: 'GET', name: 'health' },
    { url: '/api/models/status', method: 'GET', name: 'models_status' },
    { url: '/api/models/profiles', method: 'GET', name: 'models_profiles' },
    { url: '/api/models/hardware-recommendations', method: 'GET', name: 'hardware_rec' },
  ]

  apis.forEach(api => {
    apiCallCounter.add(1)
    
    const response = http.get(`http://localhost:8080${api.url}`)
    
    const success = check(response, {
      [`${api.name} responds`]: (r) => r.status === 200,
      [`${api.name} response time`]: (r) => r.timings.duration < 5000,
    })

    if (!success) {
      errorRate.add(1)
      console.error(`API ${api.name} 실패: ${response.status}`)
    } else {
      errorRate.add(0)
    }
    
    sleep(0.5) // API 간 짧은 대기
  })

  sleep(2) // 라운드 간 대기
}

export function teardown(data) {
  console.log('📊 종합 성능 테스트 완료')
  
  // 최종 상태 리포트
  const finalStatus = http.get('http://localhost:8080/api/models/status')
  if (finalStatus.status === 200) {
    const status = JSON.parse(finalStatus.body)
    console.log(`최종 모델 상태: ${status.current_profile} (${status.status})`)
    
    if (status.hardware_info?.gpus) {
      status.hardware_info.gpus.forEach((gpu, i) => {
        console.log(`GPU ${i}: ${gpu.memory_used_mb}MB / ${gpu.memory_total_mb}MB (${Math.round(gpu.memory_used_mb/gpu.memory_total_mb*100)}%)`)
      })
    }
  }
}
