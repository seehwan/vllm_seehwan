import http from 'k6/http'
import { check, sleep } from 'k6'
import { Rate, Trend } from 'k6/metrics'

// 모델 관리 API 테스트용 메트릭
const modelSwitchErrorRate = new Rate('model_switch_errors')
const modelSwitchTime = new Trend('model_switch_duration', true)

export const options = {
  // 단일 사용자로 순차적 모델 전환 테스트
  vus: 1,
  duration: '10m',
  thresholds: {
    model_switch_duration: ['p(95)<180000'], // 모델 전환 3분 이내
    model_switch_errors: ['rate<0.1'], // 전환 실패율 10% 미만
    http_req_duration: ['p(95)<5000'], // API 응답 시간
  },
}

// 테스트할 모델 프로파일들 (가벼운 모델 위주)
const testProfiles = [
  'phi3-mini',
  'deepseek-coder-7b', 
  'qwen2-7b-instruct',
  // 'deepseek-r1-distill-qwen-14b', // 14B 모델은 시간이 오래 걸림
]

export function setup() {
  console.log('🤖 모델 관리 API 성능 테스트 시작')
  
  // 초기 모델 상태 확인
  const statusResponse = http.get('http://localhost:8080/api/models/status')
  if (statusResponse.status === 200) {
    const status = JSON.parse(statusResponse.body)
    console.log(`초기 모델: ${status.current_profile}, 상태: ${status.status}`)
    return { initialModel: status.current_profile }
  }
  
  return { initialModel: 'unknown' }
}

export default function (data) {
  // 1. 모델 상태 확인 API 테스트
  const statusStartTime = Date.now()
  const statusResponse = http.get('http://localhost:8080/api/models/status')
  
  check(statusResponse, {
    'status API responds 200': (r) => r.status === 200,
    'status has required fields': (r) => {
      const body = JSON.parse(r.body)
      return body.current_profile && body.status && body.hardware_info
    },
  })

  // 2. 프로파일 목록 API 테스트
  const profilesResponse = http.get('http://localhost:8080/api/models/profiles')
  
  check(profilesResponse, {
    'profiles API responds 200': (r) => r.status === 200,
    'profiles has models list': (r) => {
      const body = JSON.parse(r.body)
      return body.profiles && Object.keys(body.profiles).length > 0
    },
  })

  // 3. 하드웨어 추천 API 테스트
  const recommendationsResponse = http.get('http://localhost:8080/api/models/hardware-recommendations')
  
  check(recommendationsResponse, {
    'recommendations API responds 200': (r) => r.status === 200,
    'has recommendation categories': (r) => {
      const body = JSON.parse(r.body)
      return body.recommended_profiles && body.compatible_profiles
    },
  })

  // 4. 모델 전환 테스트 (랜덤 모델 선택)
  const randomProfile = testProfiles[Math.floor(Math.random() * testProfiles.length)]
  const currentStatus = JSON.parse(statusResponse.body)
  
  // 이미 해당 모델이 실행 중이면 전환하지 않음
  if (currentStatus.current_profile !== randomProfile) {
    console.log(`🔄 모델 전환 시도: ${currentStatus.current_profile} → ${randomProfile}`)
    
    const switchStartTime = Date.now()
    const switchPayload = JSON.stringify({ profile_id: randomProfile })
    
    const switchResponse = http.post(
      'http://localhost:8080/api/models/switch',
      switchPayload,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: '300s', // 5분 타임아웃
      }
    )

    const switchSuccess = check(switchResponse, {
      'switch request accepted': (r) => r.status === 200,
      'switch response has message': (r) => {
        const body = JSON.parse(r.body)
        return body.success && body.message
      },
    })

    if (!switchSuccess) {
      modelSwitchErrorRate.add(1)
      console.error(`❌ 모델 전환 요청 실패: ${switchResponse.body}`)
    } else {
      modelSwitchErrorRate.add(0)
      
      // 전환 완료 대기 (폴링)
      let switchCompleted = false
      let attempts = 0
      const maxAttempts = 36 // 3분 (5초 × 36회)
      
      while (!switchCompleted && attempts < maxAttempts) {
        sleep(5) // 5초 대기
        attempts++
        
        const pollResponse = http.get('http://localhost:8080/api/models/status')
        if (pollResponse.status === 200) {
          const pollStatus = JSON.parse(pollResponse.body)
          
          if (pollStatus.status === 'running' && pollStatus.current_profile === randomProfile) {
            switchCompleted = true
            const switchDuration = Date.now() - switchStartTime
            modelSwitchTime.add(switchDuration)
            console.log(`✅ 모델 전환 완료: ${randomProfile} (${Math.round(switchDuration/1000)}초 소요)`)
            
            // 전환 완료 후 간단한 채팅 테스트
            const testChatPayload = JSON.stringify({
              messages: [{ role: 'user', content: '안녕하세요! 간단한 테스트입니다.' }],
              model: 'current',
              stream: false,
              max_tokens: 50,
            })
            
            const chatTestResponse = http.post(
              'http://localhost:8080/api/chat',
              testChatPayload,
              {
                headers: { 
                  'Content-Type': 'application/json',
                  'Authorization': 'Bearer test-token'
                },
                timeout: '30s',
              }
            )
            
            check(chatTestResponse, {
              'new model responds correctly': (r) => r.status === 200,
              'chat response has content': (r) => {
                try {
                  const body = JSON.parse(r.body)
                  return body.choices && body.choices[0] && body.choices[0].message
                } catch (e) {
                  return false
                }
              },
            })
            
          } else if (pollStatus.status === 'error') {
            console.error(`❌ 모델 전환 실패: ${pollStatus.message}`)
            modelSwitchErrorRate.add(1)
            break
          } else {
            console.log(`⏳ 모델 전환 진행 중... (${attempts}/${maxAttempts}) 상태: ${pollStatus.status}`)
          }
        }
      }
      
      if (!switchCompleted) {
        console.error(`❌ 모델 전환 타임아웃: ${randomProfile}`)
        modelSwitchErrorRate.add(1)
      }
    }
  } else {
    console.log(`ℹ️ 이미 ${randomProfile} 모델이 실행 중입니다.`)
  }

  // 5. 프로파일 재로드 테스트 (가끔씩만)
  if (Math.random() < 0.1) { // 10% 확률로 실행
    const reloadResponse = http.post('http://localhost:8080/api/models/reload')
    
    check(reloadResponse, {
      'profiles reload successful': (r) => r.status === 200,
      'reload returns updated profiles': (r) => {
        const body = JSON.parse(r.body)
        return body.success && body.profiles
      },
    })
  }

  // 테스트 간격 조정 (모델 전환은 시간이 오래 걸리므로)
  sleep(Math.random() * 10 + 5) // 5-15초 대기
}

export function teardown(data) {
  console.log('🔚 모델 관리 API 테스트 완료')
  
  // 테스트 종료 시 최종 상태 확인
  const finalStatusResponse = http.get('http://localhost:8080/api/models/status')
  if (finalStatusResponse.status === 200) {
    const finalStatus = JSON.parse(finalStatusResponse.body)
    console.log(`최종 모델: ${finalStatus.current_profile}, 상태: ${finalStatus.status}`)
  }
}
