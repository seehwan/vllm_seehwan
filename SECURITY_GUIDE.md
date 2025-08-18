# 🔒 보안 설정 가이드

## ⚠️ 중요한 보안 사항

### 환경 변수 파일 관리

- **절대 실제 보안 값을 Git에 커밋하지 마세요**
- `.env`와 `.env.local` 파일은 `.gitignore`에 의해 보호됩니다
- 실제 운영 환경에서는 시스템 환경변수나 보안 저장소를 사용하세요

### 필수 변경 사항

배포 전에 반드시 다음 값들을 변경해야 합니다:

#### 1. JWT Secret
```bash
# 강력한 JWT 서명 키 (최소 32자)
JWT_SECRET=your-super-secret-jwt-key-minimum-32-characters-long
```

#### 2. Hugging Face Token
```bash
# https://huggingface.co/settings/tokens 에서 발급
HUGGING_FACE_HUB_TOKEN=hf_your_actual_token_here
```

#### 3. Google OAuth (선택사항)
```bash
# Google Cloud Console에서 OAuth 2.0 클라이언트 생성
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_google_client_secret
```

#### 4. 데이터베이스 비밀번호
```bash
# 강력한 비밀번호 설정
POSTGRES_PASSWORD=your_very_secure_database_password_123!
```

### 보안 권장사항

1. **환경별 분리**: 개발/스테이징/운영 환경별로 다른 값 사용
2. **정기적 로테이션**: API 키와 비밀번호를 정기적으로 교체
3. **권한 최소화**: 각 서비스에 필요한 최소 권한만 부여
4. **모니터링**: 의심스러운 API 사용 패턴 모니터링

### 환경 변수 설정 방법

#### 개발 환경
```bash
cp .env.example .env.local
# .env.local 파일을 편집하여 실제 값 입력
```

#### 운영 환경
```bash
# 시스템 환경변수 또는 Docker secrets 사용
export JWT_SECRET="your-actual-secret"
export HUGGING_FACE_HUB_TOKEN="hf_your_token"
```

## 🚨 보안 사고 대응

만약 보안 키가 노출된 것 같다면:

1. **즉시 해당 키/토큰 비활성화**
2. **새로운 키/토큰 발급**
3. **Git 히스토리에서 민감한 정보 제거** (필요한 경우)
4. **관련 서비스들 재시작**
5. **로그 확인 및 피해 범위 파악**
