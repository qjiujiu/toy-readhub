from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate, UserOut, BatchUsersOut, UserUpdate
from typing import List
from app.core.biz_response import BizResponse
from app.service import user_svc
from app.storage.database import get_user_repo
from typing import Optional, Dict, List
from app.storage.user.user_interface import IUserRepository

users_router = APIRouter(prefix="/users", tags=["users"])

    
# 添加学生信息
@users_router.post("/", response_model=UserOut)
def create_user(user: UserCreate, repo: IUserRepository = Depends(get_user_repo)):
    try:
        new_user = user_svc.create_user(repo, user)
        return BizResponse(data=new_user)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 批量添加学生
@users_router.post("/batch", response_model=BatchUsersOut)
def create_batch_users(users: List[UserCreate], repo: IUserRepository = Depends(get_user_repo)):
    try:
        new_user = user_svc.create_batch_users(repo, users)
        return BizResponse(data=new_user)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


# 获取学生信息（批量查询，支持分页）
@users_router.get("/", response_model=UserOut)
def query_batch_users(page: int = 0, page_size: int = 10,  repo: IUserRepository = Depends(get_user_repo)):
    try:
        result = user_svc.get_batch_users(repo, page, page_size)
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)

# 获取学生信息（根据uid查询）
@users_router.get("/id/{uid}", response_model=UserOut)
def query_user(uid: int, repo: IUserRepository = Depends(get_user_repo)):
    try:
        user = user_svc.get_user_by_uid(repo, uid)
        return BizResponse(data=user)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 获取学生信息（根据学号查询）
@users_router.get("/sid/{student_id}", response_model=UserOut)
def get_student(student_id: str, repo: IUserRepository = Depends(get_user_repo)):
    user = user_svc.get_user_by_student_id(repo=repo, student_id=student_id)
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    return user


# 更新学生信息
@users_router.put("/{student_id}", response_model=UserOut)
def update_user(student_id: str, user_update: UserUpdate, repo: IUserRepository = Depends(get_user_repo)):
    try:
        user = user_svc.update_user(repo, student_id, user_update)
        if user:
            return BizResponse(data=user)
        else:
            return BizResponse(data=user, msg=f"updated failed: {student_id} not found.")
    
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


# 删除学生
@users_router.delete("/{student_id}", response_model=UserOut)
def delete_user(student_id: str, repo: IUserRepository = Depends(get_user_repo)):
    try:
        user = user_svc.delete_user(repo, student_id)
        return BizResponse(data=user, msg=f"delete successfully")
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)

    




    










