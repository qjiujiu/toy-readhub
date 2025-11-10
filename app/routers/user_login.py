from fastapi import APIRouter, Depends
from app.core.biz_response import BizResponse
from app.service import user_login
from app.storage.user_login.user_login_interface import IUserLoginRepository
from app.storage.user.user_interface import IUserRepository
from typing import Dict
from app.storage.database import get_userlog_repo, get_user_repo
from app.core.exceptions import InvalidCredentialsError
from app.schemas.user_login import TokenResponse, Login, UserLoginOut
from app.schemas.user import UserOut
from fastapi import Request

login_router = APIRouter(prefix="/login", tags=["login"])

@login_router.post("/user", response_model=TokenResponse)
def login_user(login_data: Login, login_repo: IUserLoginRepository = Depends(get_userlog_repo)):
    try:
        # 调用业务层的登录验证函数
        token_data = user_login.login_user(login_repo=login_repo, username=login_data.username, password=login_data.password)
        return BizResponse(data=token_data)
    except InvalidCredentialsError as e:
        return BizResponse(data=None, msg=str(e), status_code=401)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 需要鉴权的接口
@login_router.get("/me", response_model=UserOut)
def get_current_user_info(user_repo: IUserRepository = Depends(get_user_repo), request: Request = None):
    """获取当前登录的用户信息"""
    current_user = user_login.get_current_user(user_repo=user_repo, request=request)
    return current_user