from typing import Protocol, Optional, List
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate, BatchOrdersOut

class IOrderRepository(Protocol):
    # 根据订单号oid查询借阅订单
    def get_order_by_oid(self, order_id: str) -> Optional[OrderOut]:
        ...
    # 根据用户uid查询借阅订单
    def get_orders_by_uid(self, user_id: int, page: int, page_size: int) -> List[OrderOut]:
        ...
    def get_order_by_bid(self, book_id: int, page: int, page_size: int)->List[OrderOut]:
        ...

    def create_order(self, order_data: OrderCreate) -> OrderOut:
        ...

    def update_order(self, order_id: str, order_data: OrderUpdate) -> Optional[OrderOut]:
        ...

    def delete_order(self, order_id: str) -> None:
        ...

    def get_batch_orders(self, page: int, page_size: int) -> BatchOrdersOut:
        ...
