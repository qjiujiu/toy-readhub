# 封装密码哈希与 JWT：
from datetime import datetime, timedelta
from typing import Optional, Any, Dict

from jose import jwt, JWTError
from passlib.context import CryptContext
import uuid

# 强烈建议用环境变量管理
SECRET_KEY = "replace-with-your-own-secret-string"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # token有效期： 1 天
REFRESH_TOKEN_EXPIRE_DAYS = 7          # 刷新周期

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(raw_password: str) -> str:
    return pwd_context.hash(raw_password)

def verify_password(raw_password: str, password_hash: str) -> bool:
    return pwd_context.verify(raw_password, password_hash)

def _encode(payload: Dict[str, Any], minutes: Optional[int] = None, days: Optional[int] = None) -> str:
    now = datetime.utcnow()
    payload = payload.copy()
    payload["iat"] = int(now.timestamp())
    if minutes is not None:
        payload["exp"] = now + timedelta(minutes=minutes)
    if days is not None:
        payload["exp"] = now + timedelta(days=days)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(student_id: int, token_version: int) -> str:
    return _encode({"sub": str(student_id), "type": "access", "tv": token_version},
                   minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

def create_refresh_token(student_id: int, token_version: int) -> str:
    return _encode({"sub": str(student_id), "type": "refresh", "tv": token_version, "jti": str(uuid.uuid4())},
                   days=REFRESH_TOKEN_EXPIRE_DAYS)
