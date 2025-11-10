from typing import Protocol, Optional, List, Union, Dict
from app.schemas.user_login import UserLoginOut, UserLoginCreate 

class IUserLoginRepository(Protocol):
    # 根据 user_id 获取用户的登录信息
    def get_login_by_user_id(self, user_id: int) -> Optional[UserLoginOut]:
        ...

    # 根据 username 获取用户的登录信息
    def get_login_by_username(self, username: str) -> Optional[UserLoginOut]:
        ...

    # 创建新的用户登录信息
    def create_user_login(self, login_data: UserLoginCreate) -> UserLoginOut:
        ...

    # 更新用户的登录信息
    def update_user_login(self, user_id: int, login_data: UserLoginCreate) -> Optional[UserLoginOut]:
        ...

    # 根据 user_id 删除用户的登录信息
    def delete_user_login(self, user_id: int) -> None:
        ...