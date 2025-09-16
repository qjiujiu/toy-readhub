from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

# ---------- Book ----------
class BookBase(BaseModel):
    title: str
    author: str
    description: str | None = None

class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    pass

class BookOut(BookBase):
    id: int

    class Config:
        orm_mode = True

# ---------- Student ----------
# 学生模型 
class StudentBase(BaseModel):
    student_no: str
    name: str
    phone: str | None = None

class StudentCreate(StudentBase):
    password: str = Field(min_length=6, max_length=128)

class StudentRegister(BaseModel):
    student_no: str
    name: str
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = None


class StudentOut(StudentBase):
    id: int
    student_no: str
    name: str
    phone: str | None = None
    model_config = ConfigDict(from_attributes=True)

class StudentLogin(BaseModel):
    student_no: str
    password: str

# ---------- Orders ----------
# 借书订单模型
class BookOrderBase(BaseModel):
    book_id: int
    student_id: int
    borrow_date: datetime
    return_date: datetime | None = None
    status: str = "borrowed"
    

class BookOrderCreate(BookOrderBase):
    pass

class BookOrderOut(BookOrderBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ---------- Token ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshIn(BaseModel):
    refresh_token: str

class ChangePasswordIn(BaseModel):
    old_password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)