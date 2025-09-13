from pydantic import BaseModel
from datetime import datetime

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

# 学生模型 
class StudentBase(BaseModel):
    name: str
    email: str
    phone: str | None = None

class StudentCreate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: int

    class Config:
        orm_mode = True

# 借书订单模型
class BookOrderBase(BaseModel):
    book_id: int
    student_id: int
    return_date: datetime | None = None
    status: str = "borrowed"  # borrowed, returned
    

class BookOrderCreate(BookOrderBase):
    pass

class BookOrderOut(BookOrderBase):
    id: int
    borrow_date: datetime

    class Config:
        orm_mode = True