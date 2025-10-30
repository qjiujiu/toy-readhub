from typing import Protocol, Optional, List, Union, Dict
from datetime import datetime
from app.core.db import transaction
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.storage.user_restrictions.user_restrictions_interface import IUserRestrictionsRepository
from app.schemas.user_restrictions import UserRestrictionCreate, UserRestrictionUpdate, UserRestrictionOut
from app.models.user_restrictions import UserRestriction

class SQLAlchemyUserRestrictionsRepository(IUserRestrictionsRepository):
    def __init__(self, db: Session):
        self.db = db

    # 创建：新增用户限制，is_restricted默认False
    def create(self, data: UserRestrictionCreate) -> Dict:
        exist = (
            self.db.query(UserRestriction)
            .filter(UserRestriction.user_id == data.user_id)
            .one_or_none()
        )
        if exist:
            raise ValueError(f"Restriction already exists for user_id={data.user_id}")

        obj = UserRestriction(
            user_id=data.user_id,
            is_restricted=data.is_restricted,
            restricted_until=data.restricted_until,
            reason=data.reason,
        )
        with transaction(self.db):
            self.db.add(obj)
        self.db.refresh(obj)
        return UserRestrictionOut.model_validate(obj).model_dump()
    
    # 删除：按 user_id
    def delete_by_user_id(self, user_id: int) -> bool:
        row = (
            self.db.query(UserRestriction)
            .filter(UserRestriction.user_id == user_id)
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
            self.db.query(UserRestriction)
            .filter(UserRestriction.user_id == user_id)
            .one_or_none()
        )
        return None if not row else UserRestrictionOut.model_validate(row).model_dump()

    # 判断：是否受限（支持惰性解禁）
    def is_restricted(self, user_id: int, auto_clear_expired: bool = True) -> bool:
        row = (
            self.db.query(UserRestriction)
            .filter(UserRestriction.user_id == user_id)
            .one_or_none()
        )
        if not row:
            return False

        # 惰性解禁：如果已过期，顺手解除
        if auto_clear_expired and row.is_restricted and row.restricted_until:
            now = datetime.utcnow()
            if row.restricted_until <= now:
                with transaction(self.db):
                    row.is_restricted = False
                    row.restricted_until = None
                self.db.refresh(row)
                return False

        return bool(row.is_restricted)

    
    
    # 更新：按 user_id 部分更新
    def update(self, user_id: int, data: UserRestrictionUpdate) -> Optional[Dict]:
        row = (
            self.db.query(UserRestriction)
            .filter(UserRestriction.user_id == user_id)
            .one_or_none()
        )
        if not row:
            return None

        with transaction(self.db):
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(row, field, value)

        self.db.refresh(row)
        return UserRestrictionOut.model_validate(row).model_dump()



    # 惰性解禁：若过期则解除并返回最新记录
    def auto_clear_if_expired(self, user_id: int) -> Optional[Dict]:
        row = (
            self.db.query(UserRestriction)
            .filter(UserRestriction.user_id == user_id)
            .one_or_none()
        )
        if not row:
            return None

        if row.is_restricted and row.restricted_until and row.restricted_until <= datetime.utcnow():
            with transaction(self.db):
                row.is_restricted = False
                row.restricted_until = None
            self.db.refresh(row)

        return UserRestrictionOut.model_validate(row).model_dump()

    # 批量解禁：清除所有已过期限制；返回受影响条数
    def bulk_auto_clear_expired(self, now: Optional[datetime] = None) -> int:
        now = now or datetime.utcnow()
        rows = (
            self.db.query(UserRestriction)
            .filter(
                and_(
                    UserRestriction.is_restricted == True,
                    UserRestriction.restricted_until.isnot(None),
                    UserRestriction.restricted_until <= now,
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