from typing import Protocol, Optional, Dict
from datetime import datetime, timezone, timedelta
from app.core.db import transaction
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.storage.user_credit.user_credit_interface import IUserCreditRepository
from app.schemas.user_credit import UserCreditCreate, UserCreditUpdate, UserCreditOut
from app.models.user_credit import UserCredit
from app.core.logx import logger

TZ8 = timezone(timedelta(hours=8))
def _ensure_aware_local(dt: datetime, tz=TZ8) -> datetime:
    """
    若 dt 为 naive，则按本地时区tz解释（不是转换！是指定）。
    若 dt 为 aware，则转到 tz。
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)

class SQLAlchemyUserCreditRepository(IUserCreditRepository):
    def __init__(self, db: Session):
        self.db = db

    # 创建：新增用户信誉记录
    def create(self, data: UserCreditCreate) -> Dict:
        exist = (
            self.db.query(UserCredit)
            .filter(UserCredit.user_id == data.user_id)
            .one_or_none()
        )
        if exist:
            raise ValueError(f"Credit already exists for user_id={data.user_id}")

        obj = UserCredit(
            user_id=data.user_id,
            is_lost=data.is_lost,
            is_overdue=data.is_overdue,
            penalty_until=data.penalty_until,
            reason=data.reason,
        )
        with transaction(self.db):
            self.db.add(obj)
        self.db.refresh(obj)
        return UserCreditOut.model_validate(obj).model_dump()
    
    # 删除：按 user_id
    def delete_by_user_id(self, user_id: int) -> bool:
        row = (
            self.db.query(UserCredit)
            .filter(UserCredit.user_id == user_id)
            .one_or_none()
        )
        if not row:
            return False
        with transaction(self.db):
            self.db.delete(row)
        return True
    
    # 读取：按 user_id 获取
    def get_by_user_id(self, user_id: int) -> Optional[Dict]:
        row = (
            self.db.query(UserCredit)
            .filter(UserCredit.user_id == user_id)
            .one_or_none()
        )
        return None if not row else UserCreditOut.model_validate(row).model_dump()

    # 判断：是否受限
    def is_restricted(self, user_id: int) -> bool:
        row = (
            self.db.query(UserCredit)
            .filter(UserCredit.user_id == user_id)
            .one_or_none()
        )
        if not row:
            return False
        
        if row.is_lost:
            return True
        

        if row.is_overdue:
            penalty_until = row.penalty_until
            now = datetime.now(timezone(timedelta(hours=8)))
             # 统一为 aware 再比较
            try:
                rt_aware = _ensure_aware_local(penalty_until, TZ8)
            except Exception as e:
                logger.exception("normalize return_time failed: %s", e)

            if rt_aware <= now:
                with transaction(self.db):
                    row.is_overdue = False
                    row.penalty_until = None
                self.db.refresh(row)
                return False

        return bool(row.is_overdue)

    
    
    # 更新：按 user_id 部分更新
    def update(self, user_id: int, data: UserCreditUpdate) -> Optional[Dict]:
        row = (
            self.db.query(UserCredit)
            .filter(UserCredit.user_id == user_id)
            .one_or_none()
        )
        if not row:
            return None

        with transaction(self.db):
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(row, field, value)

        self.db.refresh(row)
        return UserCreditOut.model_validate(row).model_dump()



    # 惰性解禁：若过期则解除并返回最新记录
    def auto_clear_if_expired(self, user_id: int) -> Optional[Dict]:
        row = (
            self.db.query(UserCredit)
            .filter(UserCredit.user_id == user_id)
            .one_or_none()
        )
        if not row:
            return None

        if row.is_restricted and row.restricted_until and row.restricted_until <= datetime.utcnow():
            with transaction(self.db):
                row.is_restricted = False
                row.restricted_until = None
            self.db.refresh(row)

        return UserCreditOut.model_validate(row).model_dump()

    # 批量解禁：清除所有已过期限制；返回受影响条数
    def bulk_auto_clear_expired(self, now: Optional[datetime] = None) -> int:
        now = now or datetime.utcnow()
        rows = (
            self.db.query(UserCredit)
            .filter(
                and_(
                    UserCredit.is_restricted == True,
                    UserCredit.restricted_until.isnot(None),
                    UserCredit.restricted_until <= now,
                )
            )
            .all()
        )
        if not rows:
            return 0

        with transaction(self.db):
            for r in rows:
                r.is_restricted = False
                r.restricted_until = None
        return len(rows)