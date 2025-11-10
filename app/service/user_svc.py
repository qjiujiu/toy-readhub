from app.schemas.user import (
    UserCreate, 
    UserUpdate,
    UserOut,
    BatchUsersOut,
    BatchDeleteRequest,
    UserOnlyCreate
)
from app.schemas.user_credit import UserCreditCreate
from app.schemas.user_login import UserLoginCreate
from typing import Optional, Dict, List
from app.storage.user.user_interface import IUserRepository
from app.storage.user_credit.user_credit_interface import IUserCreditRepository
from app.storage.user_login.user_login_interface import IUserLoginRepository
from app.core.exceptions import StudentIDAlreadyExists, FieldRequiredError, StudentNotFound
from app.core.logx import logger

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
def create_batch_users(user_repo: IUserRepository, res_repo: IUserCreditRepository, login_repo: IUserLoginRepository, users: List[UserCreate]) -> Dict:
    new_users = []
    failed: List[Dict] = []
    
    for user_data in users:
        try:
            # 调用 create_user 来创建单个用户
            new_user = create_user(user_repo, res_repo, login_repo, user_data)
            new_users.append(new_user)
        except Exception as e:
            failed.append({"user_data": user_data.dict(), "error": str(e)})
    
    return {
        "new_users": new_users,
        "failed": failed
    }


# 创建学生
def create_user(user_repo: IUserRepository, credit_repo: IUserCreditRepository, login_repo: IUserLoginRepository, user_data: UserCreate) -> Dict:

    payload = user_data.model_dump()
    payload.pop("password", None)     # User 数据表中没有 password 字段，移除
    # 创建用户表记录
    new_user = user_repo.create_user(UserOnlyCreate(**payload))
    uid = new_user["uid"]
    # 创建用户信誉表记录
    credit_repo.create(UserCreditCreate(user_id=uid))
    login_data = UserLoginCreate(user_id=uid, username=user_data.student_id, password=user_data.password)
    # 创建用户登录记录
    login_repo.create_user_login(login_data=login_data)
    return new_user


# 更新学生基本信息
def update_user(repo: IUserRepository, student_id: str, user_data: UserUpdate) -> Optional[UserOut]:
    updated_user = repo.update_user(student_id, user_data)
    if not updated_user:
        return None
    return updated_user


# 删除学生
def delete_user(user_repo: IUserRepository, res_repo: IUserCreditRepository, login_repo: IUserLoginRepository, student_id: str) -> None:
    user = user_repo.get_user_by_student_id(student_id)
    if not user:
        raise StudentNotFound(entity="student_id", identifier=student_id)
    res_repo.delete_by_user_id(user_id=user.uid)
    login_repo.delete_user_login(user_id=user.uid)
    user_info =  user_repo.delete_user(student_id=student_id)
    return user_info

def delete_batch_users(user_repo: IUserRepository, res_repo: IUserCreditRepository, login_repo: IUserLoginRepository, student_ids: BatchDeleteRequest)-> Optional[BatchUsersOut]:
    for sid in student_ids:
        user = user_repo.get_user_by_student_id(sid)
        if not user:
             raise StudentNotFound(entity="student_id", identifier=sid)
        uid = user.uid
        res_repo.delete_by_user_id(user_id=uid)
        login_repo.delete_user_login(user_id=user.uid)
    
    result_dict = user_repo.delete_batch_users(student_ids)  # -> dict: {total, count, users: [...]}
    return BatchUsersOut.model_validate(result_dict).model_dump()



