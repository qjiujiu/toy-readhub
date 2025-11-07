from typing import Protocol, Optional, List
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate, BatchOrdersOut, OrderStatus

class IOrderRepository(Protocol):
    # 根据订单号oid查询借阅订单
    def get_order_by_oid(self, order_id: str) -> Optional[OrderOut]:
        ...

    # 根据用户uid查询借阅订单
    def get_orders_by_uid(self, user_id: int) -> List[OrderOut]:
        ...

    # 根据图书ID uid 查询借阅订单
    def get_order_by_bid(self, book_id: int)->List[OrderOut]:
        ...

    # 根据借阅状态 status 查询借阅订单
    def get_orders_by_status(self, status: OrderStatus, page: int, page_size: int) -> BatchOrdersOut:
        ...
        
    # 创建借阅订单记录
    def create_order(self, order_data: OrderCreate) -> OrderOut:
        ...

    # 更新借阅订单
    def update_order(self, order_id: str, order_data: OrderUpdate) -> Optional[OrderOut]:
        ...

    def delete_order(self, order_id: int) -> OrderOut:
        ...

    def get_batch_orders(self, page: int, page_size: int) -> BatchOrdersOut:
        ...
