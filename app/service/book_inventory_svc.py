from typing import Optional, Dict, List
from app.schemas.book_inventory import (
    BookInventoryCreate,
    BookInventoryUpdate,
    BookInventoryOut
)
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository  # 引入接口


# 根据图书ID获取图书库存信息
def get_inventory_by_book_id(repo: IBookInventoryRepository, book_id: int) -> Optional[Dict]:
    inventory = repo.get_inventory_by_book_id(book_id)
    if not inventory:
        return None
    return inventory  # 返回库存信息


# 添加一本图书的库存信息，初始库存为 1
def create_inventory(repo: IBookInventoryRepository, inventory_data: BookInventoryCreate) -> Dict:
    new_inventory = repo.create_inventory(inventory_data)
    return new_inventory  # 返回新创建的库存信息


# 修改图书库存数量
def update_inventory(repo: IBookInventoryRepository, book_id: int, inventory_data: BookInventoryUpdate) -> Optional[Dict]:
    updated_inventory = repo.update_inventory(book_id, inventory_data)
    if not updated_inventory:
        return None
    return updated_inventory  # 返回更新后的库存信息


# 删除图书库存信息
def delete_inventory(repo: IBookInventoryRepository, book_id: int) -> None:
    inventory_info = repo.delete_inventory(book_id)
    return inventory_info  # 返回删除的库存信息