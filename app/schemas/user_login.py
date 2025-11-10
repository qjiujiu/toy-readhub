from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class UserLoginOut(BaseModel):
    id: int
    user_id: int
    username: str
    password: str
    last_login: Optional[datetime] = None  # 可以根据实际需求使用 datetime 类型

    model_config = ConfigDict(from_attributes=True)



class UserLoginCreate(BaseModel):
    user_id: int
    username: str
    password: str  # 传入的密码是明文，加密后存入数据表

    model_config = ConfigDict(from_attributes=True)

class UserLoginUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None  # 传入的密码是明文，加密后存入数据表

    model_config = ConfigDict(from_attributes=True)

class Login(BaseModel):
    username: str
    password: str  # 传入的密码是明文，加密后存入数据表

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str