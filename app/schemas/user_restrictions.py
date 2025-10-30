from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.user import UserOut

class UserRestrictionCreate(BaseModel):
    """创建用户借阅限制记录的请求体"""
    user_id: int                                   # 用户ID（必填）
    is_restricted: bool = False                    # 是否被限制（默认不限制）
    restricted_until: Optional[datetime] = None    # 限制到期时间（可为空）
    reason: Optional[str] = None                   # 限制原因（可选）

    model_config = ConfigDict(from_attributes=True)

class UserRestrictionUpdate(BaseModel):
    """更新用户借阅限制信息的请求体"""
    is_restricted: Optional[bool] = None          # 是否被限制（允许更新）
    restricted_until: Optional[datetime] = None   # 限制到期时间
    reason: Optional[str] = None                  # 原因更新（可选）

    model_config = ConfigDict(from_attributes=True)

class UserRestrictionOut(BaseModel):
    """用户借阅限制记录的响应体"""
    ur_id: int
    user_id: int
    is_restricted: bool
    restricted_until: Optional[datetime]
    reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserRestrictionDetailOut(BaseModel):
    """带用户信息的借阅限制详情"""
    restriction: UserRestrictionOut
    user: UserOut

    model_config = ConfigDict(from_attributes=True)
