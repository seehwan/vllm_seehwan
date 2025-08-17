# vLLM Chat Frontend

React + Vite 기반의 vLLM 챗봇 서비스 프론트엔드입니다.

## 🛠 기술 스택

- **Framework**: React 18
- **Build Tool**: Vite 5
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **UI Components**: Radix UI
- **Markdown**: react-markdown + remark-gfm
- **Icons**: Lucide React

## 📦 주요 패키지

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.2",
    "zustand": "^4.4.6",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0",
    "lucide-react": "^0.400.0",
    "tailwind-merge": "^2.0.0",
    "@radix-ui/react-button": "^1.0.3",
    "@radix-ui/react-textarea": "^1.0.3"
  }
}
```

## 🚀 개발 환경 실행

### 필수 요구사항
- Node.js 18+ 
- npm 또는 yarn

### 초기 설정

#### 1. TypeScript 환경 설정
프로젝트에 필요한 TypeScript 설정 파일들을 생성하세요:

**`vite-env.d.ts` (Vite 환경 변수 타입 선언):**
```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_WS_URL?: string
  readonly VITE_DEBUG?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

**`tsconfig.json` (TypeScript 컴파일러 설정):**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "types": ["vite/client"]
  },
  "include": [
    "src",
    "vite-env.d.ts"
  ],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**`tsconfig.node.json` (Vite 설정 파일용):**
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

#### 2. 환경 변수 설정
`.env.local` 파일을 생성하여 환경 변수를 설정하세요:
```bash
VITE_API_BASE_URL=http://localhost:8080
VITE_DEBUG=true
```

### 로컬 개발 서버 실행
```bash
# 패키지 설치
npm install

# TypeScript 컴파일 확인
npx tsc --noEmit

# 개발 서버 실행
npm run dev

# 브라우저에서 http://localhost:3000 접속
```

### 문제 해결

#### `import.meta.env` 타입 오류
- `vite-env.d.ts` 파일이 존재하는지 확인
- VS Code에서 TypeScript 서버 재시작: `Ctrl+Shift+P` → "TypeScript: Restart TS Server"

#### Node.js 버전 문제
```bash
# Node.js 버전 확인
node --version

# 최신 LTS 버전 설치 (nvm 사용)
nvm install --lts
nvm use --lts
```

### Docker 환경에서 실행
```bash
# 프로젝트 루트에서 실행
docker compose -f docker-compose.yml -f docker-compose.dev.yml up frontend
```

## 🏗 빌드

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

## 🧪 테스트

```bash
# 단위 테스트
npm run test

# E2E 테스트
npm run test:e2e
```

## 📝 코드 품질

```bash
# ESLint 검사
npm run lint

# Prettier 코드 포매팅
npm run format
```

## 🔧 설정 파일

### Vite 설정 (`vite.config.ts`)
- React 플러그인 설정
- Path alias (`@` → `./src`)
- 프록시 설정 (API → Gateway)
- 테스트 환경 설정

### Tailwind 설정 (`tailwind.config.js`)
- 커스텀 색상 테마
- 반응형 브레이크포인트
- 애니메이션 및 키프레임

## 📁 프로젝트 구조

```
frontend/
├── public/               # 정적 파일
├── src/
│   ├── components/       # 재사용 가능한 컴포넌트
│   │   ├── ui/          # 기본 UI 컴포넌트
│   │   ├── chat/        # 채팅 관련 컴포넌트
│   │   └── layout/      # 레이아웃 컴포넌트
│   ├── hooks/           # 커스텀 훅
│   ├── store/           # Zustand 상태 관리
│   ├── types/           # TypeScript 타입 정의
│   ├── utils/           # 유틸리티 함수
│   ├── styles/          # 글로벌 스타일
│   ├── App.tsx          # 메인 애플리케이션
│   └── main.tsx         # 엔트리 포인트
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## 🔌 API 연동

### 환경변수
```env
VITE_API_BASE_URL=http://localhost:8080
```

### API 엔드포인트
- `POST /api/chat` - 채팅 스트리밍
- `GET /api/conversations` - 대화 목록
- `POST /api/conversations` - 새 대화 생성
- `GET /api/conversations/:id` - 대화 상세

## 🎨 UI/UX 특징

### 채팅 인터페이스
- **실시간 스트리밍**: SSE를 통한 실시간 응답 표시
- **마크다운 지원**: 코드 블록, 테이블, 링크 등 렌더링
- **타이핑 애니메이션**: AI 응답 중 타이핑 표시
- **다크/라이트 모드**: 테마 전환 지원

### 반응형 디자인
- 모바일, 태블릿, 데스크톱 최적화
- 터치 친화적 인터페이스
- 접근성(a11y) 고려

## 🔧 커스터마이징

### 테마 변경
`tailwind.config.js`에서 색상, 폰트, 간격 등 조정 가능

### 컴포넌트 추가
`src/components/ui/`에 새로운 UI 컴포넌트 추가

### 상태 관리 확장
`src/store/`에서 Zustand 스토어 확장

## 🐛 디버깅

### 개발자 도구
- React Developer Tools 사용 권장
- Vite 개발 서버의 HMR 활용

### 로깅
```typescript
// 개발 환경에서만 로깅
if (import.meta.env.DEV) {
  console.log('Debug info:', data);
}
```

## 📊 성능 최적화

### 번들 크기 최적화
- 코드 스플리팅 적용
- 트리 쉐이킹으로 미사용 코드 제거
- Dynamic import 활용

### 런타임 최적화
- React.memo()로 불필요한 리렌더링 방지
- useMemo, useCallback 적절히 활용
- 이미지 최적화 (WebP, 지연 로딩)

## 🚀 배포

### Docker 배포
```bash
# 프로덕션 이미지 빌드
docker build -t vllm-chat-frontend .

# 컨테이너 실행
docker run -p 3000:3000 vllm-chat-frontend
```

### Nginx 배포
빌드된 `dist/` 폴더를 Nginx 정적 서버로 배포 가능

## 🤝 기여 가이드

1. 새 기능 개발 시 컴포넌트 단위로 분리
2. TypeScript 타입 정의 철저히
3. 테스트 코드 작성 권장
4. ESLint/Prettier 규칙 준수
5. 커밋 메시지 컨벤션 따르기

## 📞 문제 해결

### 자주 발생하는 문제

**1. API 연결 실패**
- Gateway 서버 상태 확인
- CORS 설정 확인
- 프록시 설정 점검

**2. 빌드 실패**
- Node.js 버전 확인 (18+ 필요)
- 패키지 의존성 재설치: `rm -rf node_modules && npm install`

**3. 스트리밍 동작 안함**
- SSE 연결 상태 확인
- 브라우저 개발자 도구 네트워크 탭 점검

### 로그 확인
```bash
# 개발 모드 로그
docker compose logs -f frontend

# 빌드 로그
npm run build 2>&1 | tee build.log
```
