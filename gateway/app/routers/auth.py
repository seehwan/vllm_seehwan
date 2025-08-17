from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog
from ..config import settings

router = APIRouter()
logger = structlog.get_logger()
security = HTTPBearer(auto_error=False)

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


@router.get("/me", response_model=User)
async def get_current_user(current_user: dict = Depends(verify_token)):
    """현재 로그인한 사용자 정보 조회"""
    return User(
        user_id=current_user["user_id"],
        username=current_user["username"],
        email=current_user["email"]
    )
