from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import httpx
import structlog
from ..config import settings

# OAuth 관련 import는 조건부로 처리
try:
    from authlib.integrations.starlette_client import OAuth
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    OAuth = None

router = APIRouter()
logger = structlog.get_logger()
security = HTTPBearer(auto_error=False)

# OAuth 설정
oauth = None

# Starlette용 OAuth 설정 수정
def init_oauth():
    """OAuth 클라이언트 초기화"""
    global oauth
    if not OAUTH_AVAILABLE:
        return False
        
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        oauth = OAuth()
        oauth.register(
            name='google',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        return True
    return False

# OAuth 초기화
oauth_available = init_oauth()

# 패스워드 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    user_id: str
    username: str
    email: str

# 더미 사용자 데이터베이스 (실제로는 DB에서 조회)
fake_users_db = {
    "admin": {
        "user_id": "1",
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),
    },
    "test": {
        "user_id": "2", 
        "username": "test",
        "email": "test@example.com",
        "hashed_password": pwd_context.hash("test"),
    },
    "dev": {
        "user_id": "3",
        "username": "dev", 
        "email": "dev@example.com",
        "hashed_password": pwd_context.hash("dev"),
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """패스워드 검증"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """패스워드 해시 생성"""
    return pwd_context.hash(password)

def get_user(username: str):
    """사용자 조회"""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return user_dict
    return None

def authenticate_user(username: str, password: str):
    """사용자 인증"""
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """JWT 토큰 검증"""
    # 개발 환경에서 토큰이 없는 경우 기본 사용자 반환
    if settings.DEBUG or settings.ENVIRONMENT == "development":
        if not credentials:
            logger.info("개발 환경: 토큰 없이 기본 사용자 사용")
            return {
                "user_id": "dev_user",
                "username": "dev",
                "email": "dev@example.com"
            }
    
    # 토큰 검증
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        if settings.DEBUG or settings.ENVIRONMENT == "development":
            return {
                "user_id": "dev_user", 
                "username": "dev",
                "email": "dev@example.com"
            }
        raise credentials_exception
    
    try:
        # JWT 토큰 디코딩
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if username is None or user_id is None:
            logger.warning("토큰에서 사용자 정보를 찾을 수 없음")
            raise credentials_exception
            
        token_data = TokenData(username=username)
        
    except JWTError as e:
        logger.warning(f"JWT 토큰 검증 실패: {e}")
        raise credentials_exception
    
    # 사용자 정보 조회
    user = get_user(username=token_data.username)
    if user is None:
        logger.warning(f"사용자를 찾을 수 없음: {username}")
        raise credentials_exception
        
    logger.debug(f"토큰 검증 성공: {username}")
    return {
        "user_id": user["user_id"],
        "username": user["username"], 
        "email": user["email"]
    }


@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest):
    """사용자 로그인 및 JWT 토큰 발급"""
    try:
        # 개발 환경에서는 간단한 인증
        if settings.DEBUG or settings.ENVIRONMENT == "development":
            logger.info(f"개발 환경 로그인 시도: {login_request.username}")
            
            # 개발 환경에서도 기본적인 사용자 검증
            user = authenticate_user(login_request.username, login_request.password)
            if not user:
                logger.warning(f"로그인 실패: {login_request.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            # 프로덕션 환경에서는 완전한 인증
            user = authenticate_user(login_request.username, login_request.password)
            if not user:
                logger.warning(f"로그인 실패: {login_request.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # JWT 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "user_id": user["user_id"]},
            expires_delta=access_token_expires
        )
        
        logger.info(f"로그인 성공: {user['username']}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 처리 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login processing error"
        )


@router.post("/login-form", response_model=Token)
async def login_form(username: str = Form(...), password: str = Form(...)):
    """Form data를 사용한 로그인"""
    try:
        user = authenticate_user(username, password)
        if not user:
            logger.warning(f"로그인 실패: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # JWT 토큰 생성
        access_token_expires = timedelta(hours=settings.JWT_EXPIRE_HOURS)
        access_token = create_access_token(
            data={"sub": user["username"], "user_id": user["user_id"]},
            expires_delta=access_token_expires
        )
        
        logger.info(f"로그인 성공: {user['username']}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 처리 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login processing error"
        )


@router.get("/me", response_model=User)
async def get_current_user(current_user: dict = Depends(verify_token)):
    """현재 로그인한 사용자 정보 조회"""
    return User(
        user_id=current_user["user_id"],
        username=current_user["username"],
        email=current_user["email"]
    )


# Google OAuth 라우트들
@router.get("/google")
async def google_login(request: Request):
    """Google OAuth 로그인 시작"""
    if not oauth_available:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
        )
    
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request):
    """Google OAuth 콜백 처리"""
    if not oauth_available:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )
    
    try:
        # Google에서 토큰 받기
        token = await oauth.google.authorize_access_token(request)
        
        # ID 토큰에서 사용자 정보 추출
        user_info = token.get('userinfo')
        if not user_info:
            # ID 토큰 직접 파싱
            id_token_jwt = token.get('id_token')
            if id_token_jwt:
                user_info = id_token.verify_oauth2_token(
                    id_token_jwt, 
                    google_requests.Request(), 
                    settings.GOOGLE_CLIENT_ID
                )
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google"
            )
        
        # 사용자 정보 추출
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        
        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient user information from Google"
            )
        
        # 사용자 찾기 또는 생성
        user = find_or_create_oauth_user(google_id, email, name)
        
        # JWT 토큰 생성
        access_token_expires = timedelta(hours=settings.JWT_EXPIRE_HOURS)
        access_token = create_access_token(
            data={"sub": user["username"], "user_id": user["user_id"], "oauth_provider": "google"},
            expires_delta=access_token_expires
        )
        
        # 프론트엔드로 리다이렉트 (토큰과 함께)
        frontend_url = f"{settings.FRONTEND_URL}/oauth/callback?token={access_token}"
        
        logger.info(f"Google OAuth 로그인 성공: {email}")
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.error(f"Google OAuth 콜백 처리 중 오류: {e}")
        error_url = f"{settings.FRONTEND_URL}/oauth/error?error=oauth_failed"
        return RedirectResponse(url=error_url)


@router.get("/oauth/status")
async def oauth_status():
    """OAuth 설정 상태 확인 (개발용)"""
    return {
        "google_oauth_available": oauth_available,
        "google_client_id_set": bool(settings.GOOGLE_CLIENT_ID),
        "redirect_uri": settings.GOOGLE_REDIRECT_URI if oauth_available else None,
    }


def find_or_create_oauth_user(google_id: str, email: str, name: str) -> dict:
    """OAuth 사용자 찾기 또는 생성"""
    # 실제 구현에서는 데이터베이스를 사용해야 합니다
    # 여기서는 임시로 메모리에 저장
    oauth_user_id = f"google_{google_id}"
    
    # 기존 사용자 확인 (이메일 기준)
    for user_data in fake_users_db.values():
        if user_data.get("email") == email:
            # 기존 사용자에 OAuth ID 추가
            user_data["oauth_id"] = oauth_user_id
            user_data["oauth_provider"] = "google"
            return user_data
    
    # 새 사용자 생성
    new_user = {
        "user_id": oauth_user_id,
        "username": email.split("@")[0],  # 이메일의 @ 앞부분을 사용자명으로
        "email": email,
        "full_name": name,
        "oauth_id": oauth_user_id,
        "oauth_provider": "google",
        "hashed_password": None,  # OAuth 사용자는 패스워드 없음
    }
    
    # 메모리에 저장 (실제로는 DB에 저장해야 함)
    fake_users_db[email.split("@")[0]] = new_user
    
    return new_user
