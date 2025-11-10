from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from app.schemas.user_login import UserLoginCreate, UserLoginOut, UserLoginUpdate
from app.storage.user_login.user_login_interface import IUserLoginRepository
from typing import Optional
from app.models.user_login import UserLogin
from app.core.db import transaction
import bcrypt
from app.core.logx import logger

# SQLAlchemy UserLogin 仓库实现
class SQLAlchemyUserLoginRepository(IUserLoginRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_login_by_user_id(self, user_id: int) -> Optional[UserLoginOut]:
        try:
            user_login = self.db.query(UserLogin).filter(UserLogin.user_id == user_id).one()  # one() 会抛出 NoResultFound 异常
            return UserLoginOut.model_validate(user_login) if user_login else None
        except NoResultFound:
            return None

    def get_login_by_username(self, username: str) -> Optional[UserLoginOut]:
        user_login = self.db.query(UserLogin).filter(UserLogin.username == username).first()
        return UserLoginOut.model_validate(user_login) if user_login else None

    def create_user_login(self, login_data: UserLoginCreate) -> UserLoginOut:
        # 检查是否已有用户名
        existing_login = self.db.query(UserLogin).filter(UserLogin.username == login_data.username).first()
        if existing_login:
            raise ValueError(f"Username {login_data.username} already exists.")
        if not login_data.password:
            raise ValueError(f"Password is None.")
        # 对密码进行加密
        hashed_password = bcrypt.hashpw(login_data.password.encode('utf-8'), bcrypt.gensalt())

        # 创建用户登录对象，密码字段使用加密后的密码
        user_login = UserLogin(
            user_id=login_data.user_id,
            username=login_data.username,
            password=hashed_password.decode('utf-8')  # 存储为字符串
        )

        # 使用事务管理器将新增的登录信息存储到数据库
        with transaction(self.db):
            self.db.add(user_login)

        self.db.refresh(user_login)
        logger.debug(f"User login created for user_id={login_data.user_id}, username={login_data.username}")
        return UserLoginOut.model_validate(user_login).model_dump()


    def update_user_login(self, user_id: int, login_data: UserLoginUpdate) -> Optional[UserLoginOut]:
        user_login = self.db.query(UserLogin).filter(UserLogin.user_id == user_id).first()
        if not user_login:
            return None

        # 如果传入的 login_data 中有密码，先加密密码
        if 'password' in login_data.dict(exclude_unset=True):
            new_password = login_data.password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            # 更新密码为加密后的密码
            login_data.password = hashed_password.decode('utf-8')  # 存储为字符串

        # 更新用户登录信息
        with transaction(self.db):
            for field, value in login_data.dict(exclude_unset=True).items():
                setattr(user_login, field, value)

        self.db.refresh(user_login)
        return UserLoginOut.model_validate(user_login).model_dump()

    def delete_user_login(self, user_id: int) -> None:
        user_login = self.db.query(UserLogin).filter(UserLogin.user_id == user_id).first()
        if not user_login:
            raise ValueError(f"User login with user_id {user_id} not found.")

        # 使用事务管理器删除用户登录信息
        with transaction(self.db):
            self.db.delete(user_login)

        return None