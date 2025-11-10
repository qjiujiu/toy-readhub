import jwt
import datetime
from passlib.context import CryptContext
from typing import Dict
from app.core.exceptions import InvalidCredentialsError
from app.storage.user_login.user_login_interface import IUserLoginRepository
from fastapi import Request, HTTPException, Depends
from app.schemas.user_login import UserLoginOut
from app.storage.user.user_interface import IUserRepository
from app.schemas.user import UserOut

# 设置密钥和算法
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"

# 使用 Passlib 进行密码验证
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: Dict, expires_delta: datetime.timedelta = None) -> str:
    """创建JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # 默认1小时有效期
    
    to_encode.update({"exp": expire})
    # 确保 "sub" 是字符串类型
    to_encode["sub"] = str(to_encode["sub"])  # 转换为字符串
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def login_user(login_repo: IUserLoginRepository, username: str, password: str) -> Dict:
    """处理用户登录，验证账号密码并返回token"""
    # 查找用户登录信息
    user_login = login_repo.get_login_by_username(username)
    
    if not user_login:
        raise InvalidCredentialsError("Invalid username or password")
    
    # 验证密码
    if not verify_password(password, user_login.password):
        raise InvalidCredentialsError("Invalid username or password")
    
    # 创建 JWT token
    access_token = create_access_token(data={"sub": user_login.user_id})
    
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(user_repo: IUserRepository, request: Request) -> UserOut:
    """从请求中提取和验证 JWT token，返回当前用户信息"""
    # 从 Authorization 头部获取 token
    auth_header = request.headers.get("X-Access-Token")
    if not auth_header:
        raise HTTPException(status_code=401, detail="X-Access-Token is missing")
    
    token = auth_header  # 不需要 "Bearer" 前缀，直接使用完整 token

    # 解码并验证 token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # 在数据库中查找用户
        user = user_repo.get_user_by_uid(uid=user_id)  # 使用 user_repo 获取用户信息
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.exceptions.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token")