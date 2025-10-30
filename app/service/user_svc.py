from app.schemas.user import (
    UserCreate, 
    UserUpdate,
    UserOut,
    BatchUsersOut
)
from app.schemas.user_restrictions import UserRestrictionCreate
from typing import Optional, Dict, List
from app.storage.user.user_interface import IUserRepository
from app.storage.user_restrictions.user_restrictions_interface import IUserRestrictionsRepository
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
def create_batch_users(user_repo: IUserRepository, res_repo: IUserRestrictionsRepository, users: List[UserCreate]) -> Dict:

    new_users = user_repo.create_batch(users)
    restrictions_failed: List[Dict] = []
    for u in new_users:
        uid = u.get("uid")
        if uid is None:
            # 如果 data 层没有返回 uid，这是致命问题；记录并继续
            restrictions_failed.append({"uid": None, "error": "Missing uid in created_users item"})
            continue
        try:
            # 只传 user_id，其余默认：is_restricted=False, restricted_until=None, reason=None
            res_repo.create(UserRestrictionCreate(user_id=uid))
        except ValueError as e:
            # 幂等处理：如果已存在限制，就跳过
            msg = str(e)
            if "Restriction already exists" in msg or "already exists" in msg:
                continue
            else:
                restrictions_failed.append({"uid": uid, "error": msg})
        except Exception as e:
            restrictions_failed.append({"uid": uid, "error": str(e)})
    return new_users


# 创建学生
def create_user(user_repo: IUserRepository, res_repo: IUserRestrictionsRepository, user_data: UserCreate) -> Dict:
    
    # TODO 下面raise可删，不会起作用，数据库会帮忙检查必填字段是否已填入
     
    # 检查必填字段是否为空
    if not user_data.name:
        raise FieldRequiredError("name")
    if not user_data.student_id:
        raise FieldRequiredError("student_id")
    if not user_data.phone:
        raise FieldRequiredError("phone")
    new_user = user_repo.create_user(user_data)
    uid = new_user["uid"]
    res_repo.create(UserRestrictionCreate(user_id=uid))
    return new_user


# 更新学生信息
def update_user(repo: IUserRepository, student_id: str, user_data: UserUpdate) -> Optional[UserOut]:
    updated_user = repo.update_user(student_id, user_data)
    if not updated_user:
        return None
    return updated_user


# 删除学生
def delete_user(user_repo: IUserRepository, res_repo: IUserRestrictionsRepository, student_id: str) -> None:
    user = user_repo.get_user_by_student_id(student_id)
    if not user:
        raise StudentNotFound(entity="student_id", identifier=student_id)
    res_repo.delete_by_user_id(user_id=user.uid)
    user_info =  user_repo.delete_user(student_id=student_id)
    return user_info

def delete_batch_users(user_repo: IUserRepository, res_repo: IUserRestrictionsRepository, student_ids: List[str])-> Optional[BatchUsersOut]:
    for sid in student_ids:
        user = user_repo.get_user_by_student_id(sid)
        if not user:
             raise StudentNotFound(entity="student_id", identifier=sid)
        uid = user.uid
        res_repo.delete_by_user_id(user_id=uid)
        
    result_dict = user_repo.delete_batch_users(student_ids)  # -> dict: {total, count, users: [...]}
    return BatchUsersOut.model_validate(result_dict).model_dump()



