from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserOut, BatchUsersOut
from app.storage.user.user_interface import IUserRepository
from typing import Optional, List, Dict, Union
from app.core.db import transaction
from app.core.logx import logger
from fastapi import HTTPException, status
from app.core.exceptions import StudentIDAlreadyExists, FieldRequiredError
# 这是 PySQL+SQLAlchemy 实现的用户仓库(业务逻辑传入的参数是一个 IUserRepository 类型，而不是具体的子类)
# 因而可以很方便地替换为其他子类实现，比如基于 PGSQL、MongoDB 用户仓库，或是换成 MySQL 其它三方库, e.g. SQLModel 实现
class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_uid(self, uid: int) -> Optional[UserOut]:
        user = self.db.query(User).filter(User.uid == uid).first()          # query() 方法用于创建查询对象，从数据库中检索记录。
                                                                            # filter() 方法用于指定查询条件，这里根据用户id查询
                                                                            # first() 方法返回查询结果中的第一条记录，如果没有匹配的记录则返回 None
        return UserOut.model_validate(user) if user else None               # model_validate 用于将 SQLAlchemy ORM 对象转换为 Pydantic 模型的一个方法

    def get_user_by_student_id(self, student_id: str) -> Optional[UserOut]:
        user = self.db.query(User).filter(User.student_id == student_id).first()
        return UserOut.model_validate(user) if user else None

    def get_batch_users(self, page: int, page_size: int) -> List[UserOut]:
        # 获取用户列表
        users = (
            self.db.query(User)
            .offset(page * page_size)                           # offset() 方法用于跳过查询结果中的前 n 条记录，常用于分页查询，这里跳过 page * page_size 条记录
            .limit(page_size)                                   # limit() 方法用于限制查询返回的结果数
            .all()
        )
        # 获取总记录数
        total = self.db.query(User).count()                     # count() 方法用于返回查询结果的总记录数，通常用于分页计算总数
        # 返回分页后的用户信息 (由的BatchUsersOut 是一个嵌套的 Pydantic BaseModel, 故需要手动调用一下 model_dump 方法来做序列的)
        # model_dump() 把 Pydantic 对象转为 Dict
        return BatchUsersOut(total=total, count=len(users), users=users).model_dump()

    def create_user(self, user_data: UserCreate) -> UserOut:
        # 检查学号是否已存在
        existing_user = self.db.query(User).filter(User.student_id == user_data.student_id).first()
        if existing_user:
            # 如果学号已存在，抛出 StudentIDAlreadyExists 异常
            raise StudentIDAlreadyExists(user_data.student_id)
        
        user = User(**user_data.dict())

        # 使用事务管理器来将添加新用户到数据库
        with transaction(self.db):
            self.db.add(user)                                   # add() 方法将对象添加到会话中(待插入，未提交)
        
        self.db.refresh(user)                                   # refresh() 方法会从数据库重新加载对象，确保user对象的内容是最新的
        return UserOut.model_validate(user).model_dump()

    def create_batch(self, users: List[UserCreate]) -> List[UserOut]:
        user_orms = [User(**u.dict()) for u in users]
        # 使用事务管理器批量添加用户
        with transaction(self.db):
            self.db.add_all(user_orms)                          # add_all() 方法与 add() 类似，用于一次性添加多个对象。
        
        # 调用 refresh 处理的实体，必须是已经在库内的实体(因而创建操作需要先做commit 才能刷新)
        for user in user_orms:
            self.db.refresh(user)
        return [UserOut.model_validate(user).model_dump() for user in user_orms]

    def update_user(self, student_id: str, user_data: UserUpdate) -> Optional[UserOut]:
        user = self.db.query(User).filter(User.student_id == student_id).first()
        if not user:
            return None
        
        # 使用事务管理器, 刷新用户信息，确保数据库中的数据更新到最新
        with transaction(self.db):
            # 更新用户属性
            for field, value in user_data.dict(exclude_unset=True).items():
                setattr(user, field, value)                     # 把 user 对象的 field 属性名对应的属性值设置为 value
        
        self.db.refresh(user)
        return UserOut.model_validate(user).model_dump()

    def delete_user(self, student_id: str) -> None:
        user = self.db.query(User).filter(User.student_id == student_id).first()
        if not user:
            raise ValueError(f"User with student_id {student_id} not found.")
        
        # 使用事务管理器
        with transaction(self.db):
            self.db.delete(user)  # 删除用户

        return UserOut.model_validate(user).model_dump()
    
    # 批量删除用户：按 student_id 列表
    def delete_batch_users(self, student_ids: List[str]) -> Dict:
        if not student_ids:
            raise ValueError("student_ids list cannot be empty.")
        # logger.debug("RAW student_ids: %s", [repr(x) for x in student_ids])
        # 查询所有待删除用户
        users = (self.db.query(User).filter(User.student_id.in_(student_ids)).all())
        # 检查是否有缺失的 student_id
        found_ids = {u.student_id for u in users}
        # logger.debug("DB found_ids: %s", [repr(x) for x in found_ids])
        missing_ids = [sid for sid in student_ids if sid not in found_ids]

        if missing_ids:
            # 如果有不存在的学号，直接报错
            raise ValueError(
                f"The following student_ids were not found in database: {', '.join(missing_ids)}"
            )

        total = len(student_ids)
        count = len(users)

        # 预生成返回快照（删除后不能再 refresh）
        users_snapshot = [UserOut.model_validate(u).model_dump() for u in users]

        # 批量删除
        with transaction(self.db):
            for u in users:
                self.db.delete(u)

        # 返回结构体
        result = BatchUsersOut(
            total=total,
            count=count,
            users=users_snapshot
        )
        return result
    
