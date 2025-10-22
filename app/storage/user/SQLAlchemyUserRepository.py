from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserOut, BatchUsersOut
from app.storage.user.user_interface import IUserRepository
from typing import Optional, List, Dict, Union
from app.core.db import transaction


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