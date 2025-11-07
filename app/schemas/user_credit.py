from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.user import UserOut

class UserCreditCreate(BaseModel):
    """创建用户借阅限制记录的请求体"""
    user_id: int                                   # 用户ID（必填）
    is_lost: bool = False                          # 用户是否丢失图书（默认不限制）
    is_overdue: bool = False                       # 用户是否逾期还书（默认不限制）
    penalty_until: Optional[datetime] = None       # 惩罚到期时间（可为空）
    return_due_at: Optional[datetime] = None       # 还书到期时间（可为空）
    reason: Optional[str] = None                   # 限制原因（可选）

    model_config = ConfigDict(from_attributes=True)

class UserCreditUpdate(BaseModel):
    """更新用户借阅限制信息的请求体"""
    is_lost: Optional[bool] = None                # 用户是否归还丢失图书（允许更新）
    is_overdue: Optional[bool] = None             # 用户是否归还逾期还书
    penalty_until: Optional[datetime] = None      # 惩罚到期时间
    return_due_at: Optional[datetime] = None      # 还书到期时间
    reason: Optional[str] = None                  # 原因更新（可选）

    model_config = ConfigDict(from_attributes=True)

class UserCreditOut(BaseModel):
    """用户借阅限制记录的响应体"""
    uc_id: int
    user_id: int
    is_lost: bool = False                          # 用户是否丢失图书（默认不限制）
    is_overdue: bool = False                       # 用户是否逾期还书（默认不限制）
    penalty_until: Optional[datetime] = None       # 惩罚到期时间（可为空）
    return_due_at: Optional[datetime] = None       # 还书到期时间（可为空）
    reason: Optional[str] = None                   # 限制原因（可选）
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserCreditDetailOut(BaseModel):
    """带用户信息的借阅限制详情"""
    restriction: UserCreditOut
    user: UserOut

    model_config = ConfigDict(from_attributes=True)
