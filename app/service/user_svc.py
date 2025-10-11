from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import (
    UserCreate, 
    UserUpdate,
    UserOut
)

from typing import Optional, Dict, List
from app.storage.user.user_interface import IUserRepository

# 批量查询学生（可分页）
def get_batch_users(repo: IUserRepository, page: int = 0, page_size: int = 10) -> Dict:    
    return repo.get_batch_users(page=page, page_size=page_size)


# 基于技术逐主键 uid 获取学生
def get_user_by_uid(repo: IUserRepository, uid: int, to_dict: bool = True) -> Optional[Dict]:
    user = repo.get_user_by_uid(uid)
    if not user:
        return None
    return user.model_dump() if to_dict and user else user            # model_dump() 是用于将对象转换为字典的一个方法，这里将 user 转为字典格式

# 根据业务主键学号获取学生
def get_user_by_student_id(repo: IUserRepository,  student_id: str, to_dict: bool = True) -> Optional[Dict]:
    user = repo.get_user_by_student_id(student_id)
    if not user:
        return None
    return user.model_dump() if to_dict else user


# 批量创建学生
def create_batch_users(repo: IUserRepository, users: List[UserCreate]) -> Dict:
    new_users = repo.create_batch(users)
    return new_users


# 创建学生
def create_user(repo: IUserRepository, user_data: UserCreate) -> Dict:
    new_user = repo.create_user(user_data)
    return new_user


# 更新学生信息
def update_user(repo: IUserRepository, student_id: str, user_data: UserUpdate) -> Optional[UserOut]:
    updated_user = repo.update_user(student_id, user_data)
    if not updated_user:
        return None
    return updated_user


# 删除学生
def delete_user(repo: IUserRepository, student_id: str) -> None:
    user_info =  repo.delete_user(student_id)
    return user_info



