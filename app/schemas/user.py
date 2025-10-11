from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Dict

class UserOut(BaseModel):
    uid: int
    name: str
    student_id: str
    email: Optional[EmailStr]
    phone: str

    # 如果开启这个配置，此处的 schemas 里面的 Pydantic 模型会自动调用 from_orm 方法来将 ORM 对象转换为 Pydantic 对象
    # 通常只有需要输出的结构，也就是需要作为接口返回值的结构，（带有out后缀的）才需要增加这个配置
    model_config = ConfigDict(from_attributes=True)


class BatchUsersOut(BaseModel):
    total: int
    count: int
    users: List[UserOut]

    model_config = ConfigDict(from_attributes=True)
    

class UserCreate(BaseModel):
    name: str
    student_id: str
    email: Optional[EmailStr] = None
    phone: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


