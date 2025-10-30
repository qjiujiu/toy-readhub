from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.book import BookOut
from app.schemas.user import UserOut

from enum import Enum
# 可选：在应用层用 Enum 来校验和限制状态值（不直接映射数据库 Enum）
# 在业务层约束方便后续修改
# 倘若在数据库层约束，需要打开Navicat，更新约束，然后把存量的数据批量更新
class OrderStatus(str, Enum):
    borrowed = "borrowed"
    returned = "returned"
    lost = "lost"
    lost_and_returned = "lost_and_returned"  # 新增丢失归还状态

# 创建借阅订单的请求体
class OrderCreate(BaseModel):
    user_id: int                                # 借阅人ID
    book_id: int                                # 图书ID
    warehouse_name: str                         # 所借书所在图书馆/仓库
    status: OrderStatus = OrderStatus.borrowed  # 借阅状态，默认为借阅中

    model_config = ConfigDict(from_attributes=True)


# 返回的借阅订单信息
class OrderOut(BaseModel):
    order_id: int                # 借阅订单号
    user_id: int                 # 借阅人ID
    book_id: int                 # 图书ID
    warehouse_name: str          # 所借书所在图书馆/仓库
    status: OrderStatus          # 借阅状态
    borrow_time: datetime        # 借书时间
    return_time: Optional[datetime]  # 归还时间（可为空）

    # 嵌套的书籍和用户信息
    book: BookOut                # 图书信息（嵌套BookOut）
    user: UserOut                # 借阅人信息（嵌套UserOut）

    # model_config = ConfigDict(from_attributes=True)
    model_config = {
        "from_attributes": True,  
        "json_encoders": {datetime: lambda v: v.isoformat() if v else None}
    }
    


# 更新借阅订单的请求体
class OrderUpdate(BaseModel):
    status: Optional[OrderStatus]    # 更新借阅状态（可选）
    return_time: Optional[datetime]  # 归还时间（可选）

    model_config = ConfigDict(from_attributes=True)

# 批量返回借阅订单信息的响应体
class BatchOrdersOut(BaseModel):
    total: int                        # 总记录数
    count: int                        # 当前返回的记录数
    orders: list[OrderOut]            # 借阅订单列表

    model_config = ConfigDict(from_attributes=True)
