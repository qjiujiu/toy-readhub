from typing import Protocol, Optional, List
from app.schemas.book_inventory import BookInventoryCreate, BookInventoryUpdate, BookInventoryOut

class IBookInventoryRepository(Protocol):
    # 根据图书ID获取图书库存信息
    def get_inventory_by_book_id(self, book_id: int) -> Optional[BookInventoryOut]:
        ...

    # 根据图书ID和校区信息获取图书库存信息
    def get_by_bid_and_warehouse(self, book_id: int, warehouse_name: str)-> Optional[BookInventoryOut]:
        ...

    # 根据图书ID和校区信息增加库存数量（默认+1）
    def increment_quantity(self, book_id: int, warehouse_name: str, delta: int = 1)->Optional[BookInventoryOut]:
        ...

    # 添加一本图书的库存信息，初始库存为 1
    def create_inventory(self, inventory_data: BookInventoryCreate) -> BookInventoryOut:
        ...

    # 修改图书库存数量
    def update_inventory(self, book_id: int, inventory_data: BookInventoryUpdate) -> Optional[BookInventoryOut]:
        ...

    # 删除图书库存信息
    def delete_inventory(self, book_id: int) -> None:
        ...
