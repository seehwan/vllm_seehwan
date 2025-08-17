# 🧪 vLLM 서비스 테스트 가이드

포괄적인 테스트 전략과 실행 방법을 다루는 가이드입니다.

## 🎯 테스트 전략

### **테스트 피라미드**
```
        🔺 E2E Tests (5%)
       /   전체 시스템 통합
      /
     🔺 Integration Tests (15%)  
    /   API + Database + vLLM
   /
  🔺 Unit Tests (80%)
 /   개별 함수/컴포넌트
```

### **테스트 분류**

1. **Unit Tests** - 개별 함수/클래스/컴포넌트
2. **Integration Tests** - 모듈 간 연동
3. **API Tests** - REST API 엔드포인트  
4. **Performance Tests** - 부하/성능
5. **E2E Tests** - 사용자 시나리오

---

## 🔧 Backend 테스트 (Gateway)

### **환경 설정**

```bash
cd gateway

# 테스트 의존성 설치
pip install pytest pytest-asyncio httpx pytest-cov

# 테스트 데이터베이스 설정
export TEST_DATABASE_URL="postgresql+asyncpg://test:test@localhost:5433/test_chatdb"
```

### **Unit Tests**

```python
# tests/unit/test_model_manager.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.model_manager import VLLMModelManager
from app.schemas.model import ModelProfile

@pytest.fixture
def model_manager():
    return VLLMModelManager()

@pytest.fixture  
def sample_profile():
    return ModelProfile(
        name="Test Model",
        model_id="test/model",
        description="Test model for unit tests",
        max_model_len=2048,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.8,
        dtype="float16",
        swap_space=2,
        hardware_requirements={
            "min_vram_gb": 8,
            "recommended_vram_gb": 16
        }
    )

@pytest.mark.asyncio
async def test_get_hardware_info(model_manager):
    """GPU 하드웨어 정보 조회 테스트"""
    with patch('subprocess.run') as mock_run:
        # nvidia-smi 명령어 결과 모킹
        mock_run.return_value.stdout = """
0, GeForce RTX 3090, 24576, 2048, 93
1, GeForce RTX 3090, 24576, 1024, 45
        """.strip()
        mock_run.return_value.returncode = 0
        
        hardware_info = await model_manager._get_hardware_info()
        
        assert hardware_info["gpu_count"] == 2
        assert hardware_info["total_vram_gb"] == 48.0
        assert len(hardware_info["gpus"]) == 2
        assert hardware_info["gpus"][0]["name"] == "GeForce RTX 3090"

def test_check_hardware_compatibility(model_manager, sample_profile):
    """하드웨어 호환성 검증 테스트"""
    hardware_info = {
        "gpu_count": 2,
        "total_vram_gb": 48.0,
        "available_vram_gb": 45.0
    }
    
    compatibility = model_manager._check_hardware_compatibility(sample_profile, hardware_info)
    
    assert compatibility["compatible"] is True
    assert "sufficient_vram" in compatibility
    assert "sufficient_gpus" in compatibility

@pytest.mark.asyncio
async def test_model_switch_success(model_manager):
    """모델 전환 성공 시나리오 테스트"""
    with patch.object(model_manager, '_get_hardware_info') as mock_hardware, \
         patch.object(model_manager, '_restart_vllm_container') as mock_restart, \
         patch.object(model_manager, '_wait_for_model_ready') as mock_wait:
        
        mock_hardware.return_value = {"gpu_count": 2, "available_vram_gb": 45.0}
        mock_restart.return_value = True
        mock_wait.return_value = True
        
        # 테스트용 프로파일 추가
        model_manager.profiles["test-model"] = sample_profile
        
        result = await model_manager.switch_model("test-model")
        
        assert result is True
        assert model_manager.current_profile == "test-model"
        assert model_manager.status == "running"

@pytest.mark.asyncio
async def test_model_switch_incompatible_hardware(model_manager, sample_profile):
    """하드웨어 비호환 시 모델 전환 실패 테스트"""
    with patch.object(model_manager, '_get_hardware_info') as mock_hardware:
        mock_hardware.return_value = {"gpu_count": 1, "available_vram_gb": 4.0}
        
        model_manager.profiles["test-model"] = sample_profile
        
        result = await model_manager.switch_model("test-model")
        
        assert result is False
        assert model_manager.status == "error"
```

### **Integration Tests**

```python
# tests/integration/test_models_api.py
import pytest
from fastapi.testclient import TestClient
import asyncio

from app.main import app
from app.services.model_manager import model_manager

client = TestClient(app)

@pytest.fixture(autouse=True)
async def reset_model_manager():
    """각 테스트 전에 모델 매니저 상태 초기화"""
    model_manager.current_profile = None
    model_manager.status = "stopped"
    yield
    # 테스트 후 정리 작업

def test_get_model_status():
    """모델 상태 API 테스트"""
    response = client.get("/api/models/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "current_profile" in data
    assert "status" in data
    assert "available_profiles" in data
    assert "hardware_info" in data

def test_get_model_profiles():
    """모델 프로파일 목록 API 테스트"""
    response = client.get("/api/models/profiles")
    assert response.status_code == 200
    
    data = response.json()
    assert "profiles" in data
    assert "current_profile" in data
    assert isinstance(data["profiles"], dict)
    assert len(data["profiles"]) > 0

def test_model_switch_nonexistent_profile():
    """존재하지 않는 모델 전환 시 오류 처리"""
    response = client.post(
        "/api/models/switch",
        json={"profile_id": "nonexistent-model"}
    )
    assert response.status_code == 404

def test_get_hardware_recommendations():
    """하드웨어 추천 API 테스트"""
    response = client.get("/api/models/hardware-recommendations")
    assert response.status_code == 200
    
    data = response.json()
    assert "current_hardware" in data
    assert "recommended_profiles" in data
    assert "compatible_profiles" in data
    assert "incompatible_profiles" in data

def test_reload_profiles():
    """프로파일 재로드 API 테스트"""
    response = client.post("/api/models/reload")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "profiles" in data
```

### **API 성능 테스트**

```python
# tests/performance/test_api_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import requests

BASE_URL = "http://localhost:8080"

def test_model_status_response_time():
    """모델 상태 API 응답 시간 테스트"""
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/api/models/status")
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # 1초 이내 응답

def test_concurrent_api_calls():
    """동시 API 호출 성능 테스트"""
    def make_request():
        return requests.get(f"{BASE_URL}/api/models/status")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        start_time = time.time()
        futures = [executor.submit(make_request) for _ in range(50)]
        responses = [future.result() for future in futures]
        end_time = time.time()
    
    # 모든 요청이 성공해야 함
    for response in responses:
        assert response.status_code == 200
    
    # 50개 요청이 5초 이내에 완료되어야 함
    assert (end_time - start_time) < 5.0
    
    # 평균 응답 시간 확인
    avg_time = (end_time - start_time) / len(responses)
    assert avg_time < 0.1  # 평균 100ms 이내

def test_chat_api_performance():
    """채팅 API 성능 테스트 (스트리밍 제외)"""
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "current",
        "stream": False
    }
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers={"Authorization": "Bearer test-token"}
    )
    end_time = time.time()
    
    assert response.status_code == 200
    response_time = end_time - start_time
    
    # TTFT (Time to First Token) 목표: 2초 이내
    assert response_time < 2.0
```

---

## 🎨 Frontend 테스트

### **환경 설정**

```bash
cd frontend

# 테스트 의존성 설치
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event vitest jsdom

# Vitest 설정 추가 (vite.config.ts)
```

### **컴포넌트 단위 테스트**

```typescript
// src/components/chat/__tests__/ModelSelector.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ModelSelector } from '../ModelSelector';

const mockModels = {
  "deepseek-r1-distill-qwen-14b": {
    name: "DeepSeek R1 Distill Qwen 14B",
    description: "최신 DeepSeek R1 distilled 모델"
  },
  "phi3-mini": {
    name: "Phi-3 Mini 3.8B",
    description: "Microsoft 경량 모델"
  }
};

const mockOnModelChange = jest.fn();

describe('ModelSelector', () => {
  beforeEach(() => {
    mockOnModelChange.mockClear();
  });

  test('모델 목록이 올바르게 렌더링된다', () => {
    render(
      <ModelSelector
        models={mockModels}
        currentModel="deepseek-r1-distill-qwen-14b"
        onModelChange={mockOnModelChange}
        isLoading={false}
      />
    );

    expect(screen.getByText('DeepSeek R1 Distill Qwen 14B')).toBeInTheDocument();
    expect(screen.getByText('Phi-3 Mini 3.8B')).toBeInTheDocument();
  });

  test('모델 선택 시 콜백이 호출된다', async () => {
    const user = userEvent.setup();
    
    render(
      <ModelSelector
        models={mockModels}
        currentModel="deepseek-r1-distill-qwen-14b"
        onModelChange={mockOnModelChange}
        isLoading={false}
      />
    );

    const selectButton = screen.getByRole('button');
    await user.click(selectButton);

    const phi3Option = screen.getByText('Phi-3 Mini 3.8B');
    await user.click(phi3Option);

    expect(mockOnModelChange).toHaveBeenCalledWith('phi3-mini');
  });

  test('로딩 상태에서 비활성화된다', () => {
    render(
      <ModelSelector
        models={mockModels}
        currentModel="deepseek-r1-distill-qwen-14b"
        onModelChange={mockOnModelChange}
        isLoading={true}
      />
    );

    const selectButton = screen.getByRole('button');
    expect(selectButton).toBeDisabled();
    expect(screen.getByText('전환 중...')).toBeInTheDocument();
  });
});
```

### **통합 테스트**

```typescript
// src/hooks/__tests__/useModelManagement.test.ts
import { renderHook, act } from '@testing-library/react';
import { useModelManagement } from '../useModelManagement';

// API 모킹
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('useModelManagement', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  test('모델 상태를 올바르게 가져온다', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        current_profile: 'deepseek-r1-distill-qwen-14b',
        status: 'running',
        available_profiles: mockModels
      })
    });

    const { result } = renderHook(() => useModelManagement());

    await act(async () => {
      await result.current.fetchModelStatus();
    });

    expect(result.current.currentModel).toBe('deepseek-r1-distill-qwen-14b');
    expect(result.current.status).toBe('running');
  });

  test('모델 전환이 올바르게 동작한다', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        message: '모델 전환을 시작합니다'
      })
    });

    const { result } = renderHook(() => useModelManagement());

    await act(async () => {
      await result.current.switchModel('phi3-mini');
    });

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8080/api/models/switch',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ profile_id: 'phi3-mini' })
      })
    );
  });
});
```

---

## 🚀 E2E 테스트 (Playwright)

### **환경 설정**

```bash
# Playwright 설치
npm init playwright@latest

# 테스트 실행
npx playwright test
```

### **사용자 시나리오 테스트**

```typescript
// tests/e2e/model-management.spec.ts
import { test, expect } from '@playwright/test';

test.describe('모델 관리 E2E 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('모델 선택 및 전환 전체 플로우', async ({ page }) => {
    // 1. 현재 모델 상태 확인
    await expect(page.locator('[data-testid="current-model"]')).toBeVisible();
    
    // 2. 모델 선택 드롭다운 열기
    await page.click('[data-testid="model-selector"]');
    
    // 3. 사용 가능한 모델 목록 확인
    await expect(page.locator('[data-testid="model-option"]')).toHaveCount(10);
    
    // 4. 다른 모델 선택
    await page.click('[data-testid="model-option-phi3-mini"]');
    
    // 5. 전환 중 상태 확인
    await expect(page.locator('text=전환 중')).toBeVisible();
    
    // 6. 전환 완료 대기 (최대 3분)
    await expect(page.locator('text=전환 완료')).toBeVisible({ timeout: 180000 });
    
    // 7. 새 모델로 채팅 테스트
    await page.fill('[data-testid="chat-input"]', '안녕하세요!');
    await page.click('[data-testid="send-button"]');
    
    // 8. AI 응답 확인
    await expect(page.locator('[data-testid="ai-message"]').first()).toBeVisible({ timeout: 10000 });
  });

  test('호환되지 않는 모델 선택 시 경고 표시', async ({ page }) => {
    // GPU 메모리가 부족한 상황을 시뮬레이션
    await page.route('**/api/models/hardware-recommendations', async route => {
      await route.fulfill({
        json: {
          current_hardware: { available_vram_gb: 8 },
          compatible_profiles: ['phi3-mini'],
          incompatible_profiles: ['llama3-70b-instruct']
        }
      });
    });

    await page.reload();
    await page.click('[data-testid="model-selector"]');
    
    // 호환되지 않는 모델은 비활성화되어야 함
    await expect(page.locator('[data-testid="model-option-llama3-70b-instruct"]')).toHaveClass(/disabled/);
    
    // 경고 메시지 확인
    await page.hover('[data-testid="model-option-llama3-70b-instruct"]');
    await expect(page.locator('text=현재 하드웨어로 실행할 수 없습니다')).toBeVisible();
  });
});
```

---

## 📊 테스트 실행 및 리포팅

### **테스트 실행 명령어**

```bash
# Backend 테스트
cd gateway
pytest tests/ -v --cov=app --cov-report=html

# Frontend 테스트  
cd frontend
npm run test

# E2E 테스트
npx playwright test

# 성능 테스트
cd k6
k6 run load-test.js
```

### **CI/CD 파이프라인 통합**

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_chatdb
    
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd gateway
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        cd gateway
        pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./gateway/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd frontend
        npm install
    
    - name: Run tests
      run: |
        cd frontend
        npm run test:coverage

  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install Playwright
      run: |
        cd frontend
        npx playwright install
    
    - name: Start services
      run: |
        docker compose -f docker-compose.yml -f docker-compose.test.yml up -d
        sleep 30  # 서비스 시작 대기
    
    - name: Run E2E tests
      run: |
        cd frontend  
        npx playwright test
    
    - name: Upload test results
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: playwright-report
        path: frontend/playwright-report/
```

### **테스트 커버리지 목표**

- **Backend**: 80% 이상
- **Frontend**: 70% 이상  
- **E2E**: 주요 사용자 시나리오 100% 커버
- **Performance**: 응답시간 SLA 100% 달성

---

## 🔍 테스트 모범 사례

### **좋은 테스트 작성법**

1. **AAA 패턴**: Arrange, Act, Assert
2. **독립성**: 각 테스트는 독립적으로 실행 가능
3. **재현성**: 항상 같은 결과 보장
4. **가독성**: 테스트 이름과 내용이 명확
5. **빠른 실행**: 단위 테스트는 빠르게

### **테스트 데이터 관리**

```python
# tests/fixtures/model_fixtures.py
@pytest.fixture
def sample_model_profiles():
    return {
        "test-small": {
            "name": "Test Small Model",
            "model_id": "microsoft/DialoGPT-small",
            "hardware_requirements": {"min_vram_gb": 2}
        },
        "test-large": {
            "name": "Test Large Model", 
            "model_id": "test/large-model",
            "hardware_requirements": {"min_vram_gb": 32}
        }
    }
```

### **Mock 전략**

```python
# 외부 의존성은 항상 mock
@patch('subprocess.run')  # nvidia-smi 호출
@patch('docker.from_env')  # Docker API 호출
@patch('httpx.AsyncClient.post')  # HTTP 요청
```

---

## ✅ 테스트 체크리스트

### **개발 중**
- [ ] 새 기능에 대한 단위 테스트 작성
- [ ] 기존 테스트가 통과하는지 확인
- [ ] 테스트 커버리지 확인

### **PR 제출 전**
- [ ] 전체 테스트 스위트 실행
- [ ] E2E 테스트 통과 확인
- [ ] 성능 테스트 확인
- [ ] 코드 커버리지 목표 달성

### **배포 전**
- [ ] 프로덕션 유사 환경에서 테스트
- [ ] 부하 테스트 통과
- [ ] 롤백 시나리오 테스트

---

## 📈 지속적 개선

### **테스트 메트릭 추적**
- 테스트 실행 시간
- 커버리지 변화 추이
- 플레이키 테스트 식별
- 버그 발견율

### **정기 리뷰**
- 월간 테스트 전략 리뷰
- 새로운 테스트 도구 도입 검토
- 팀 피드백 수집 및 반영

이 테스트 가이드를 통해 높은 품질의 안정적인 vLLM 서비스를 유지할 수 있습니다! 🚀
