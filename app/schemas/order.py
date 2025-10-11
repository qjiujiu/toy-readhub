from pydantic import BaseModel, constr, condecimal
from typing import Optional
from datetime import datetime
from app.schemas.book import BookOut
from app.schemas.user import UserOut

from enum import Enum
class OrderStatus(str, Enum):
    borrowed = "borrowed"
    returned = "returned"
    lost = "lost"


# 创建借阅订单的请求体
class OrderCreate(BaseModel):
    user_id: int                  # 借阅人ID
    book_id: int                  # 图书ID
    warehouse_name: str           # 所借书所在图书馆/仓库
    status: OrderStatus = OrderStatus.borrowed  # 借阅状态，默认为借阅中
    borrow_time: datetime = datetime.utcnow()  # 借书时间，默认为当前时间
    return_time: Optional[datetime] = None     # 归还时间，默认为空

    class Config:
        orm_mode = True  # 启用 orm_mode 支持从 ORM 模型实例创建 Pydantic 模型


# 返回的借阅订单信息
class OrderOut(BaseModel):
    order_id: str                # 借阅订单号
    user_id: int                 # 借阅人ID
    book_id: int                 # 图书ID
    warehouse_name: str          # 所借书所在图书馆/仓库
    status: OrderStatus          # 借阅状态
    borrow_time: datetime        # 借书时间
    return_time: Optional[datetime]  # 归还时间（可为空）

    # 嵌套的书籍和用户信息
    book: BookOut                # 图书信息（嵌套BookOut）
    user: UserOut                # 借阅人信息（嵌套UserOut）

    class Config:
        orm_mode = True  # 启用 orm_mode 支持从 ORM 模型实例创建 Pydantic 模型


# 更新借阅订单的请求体
class OrderUpdate(BaseModel):
    status: Optional[OrderStatus]    # 更新借阅状态（可选）
    return_time: Optional[datetime]  # 归还时间（可选）

    class Config:
        orm_mode = True  # 启用 orm_mode 支持从 ORM 模型实例创建 Pydantic 模型


# 批量返回借阅订单信息的响应体
class BatchOrdersOut(BaseModel):
    total: int                        # 总记录数
    count: int                        # 当前返回的记录数
    orders: list[OrderOut]            # 借阅订单列表

    class Config:
        orm_mode = True  # 启用 orm_mode 支持从 ORM 模型实例创建 Pydantic 模型
