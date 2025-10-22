from sqlalchemy.orm import Session
from app.models.book_inventory import BookInventory  # 图书库存模型
from app.schemas.book_inventory import BookInventoryCreate, BookInventoryUpdate, BookInventoryOut
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from typing import Optional, Dict, List
from app.core.db import transaction
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import selectinload
class SQLAlchemyBookinvRepository(IBookInventoryRepository):
    def __init__(self, db: Session):
        self.db = db  # 数据库会话对象

    # 根据图书ID获取图书库存信息
    def get_inventory_by_book_id(self, book_id: int) -> Optional[BookInventoryOut]:
        # 查找图书库存信息，基于图书的ID
        inventory = self.db.query(BookInventory).filter(BookInventory.book_id == book_id).first()
        if inventory:
            return BookInventoryOut.model_validate(inventory).model_dump()  # 返回图书库存信息
        return None  # 若没有找到对应的库存信息，返回 None


    def get_by_bid_and_warehouse(self, book_id: int, warehouse_name: str) -> Optional[dict]:
        name = (warehouse_name or "").strip()
        inv = (
            self.db.query(BookInventory)
            .options(selectinload(BookInventory.book))  # 关键：加载嵌套对象
            .filter(BookInventory.book_id == book_id,
                    BookInventory.warehouse_name == name)
            .one_or_none()
        )
        if not inv:
            return None
        return BookInventoryOut.model_validate(inv).model_dump()


    # 根据图书ID和仓库名称增加库存数量（默认 +1）
    def increment_quantity(self, book_id: int, warehouse_name: str, delta: int = 1) -> Optional[dict]:
        inv = (
            self.db.query(BookInventory)
            .options(selectinload(BookInventory.book))
            .filter(BookInventory.book_id == book_id,
                    BookInventory.warehouse_name == warehouse_name.strip())
            .one_or_none()
        )
        if not inv:
            return None
        inv.quantity += delta
        with transaction(self.db):
            self.db.add(inv)
        self.db.refresh(inv)
        return BookInventoryOut.model_validate(inv).model_dump()

    
    # 添加一本图书的库存信息，初始库存为 1
    def create_inventory(self, inventory_data: BookInventoryCreate) -> dict:
        inv = BookInventory(
            book_id=inventory_data.book_id,
            warehouse_name=inventory_data.warehouse_name,
            quantity=1
        )
        with transaction(self.db):
            self.db.add(inv)
        # 确保关系可用（当前会话中 inv.book 会被懒加载；为安全也可 selectinload 重新查一次）
        self.db.refresh(inv)
        _ = inv.book  # 触发加载（若未加载）
        return BookInventoryOut.model_validate(inv).model_dump()

    # 修改图书库存数量
    def update_inventory(self, book_id: int, inventory_data: BookInventoryUpdate) -> Optional[BookInventoryOut]:
        # 查找库存记录
        inventory = self.db.query(BookInventory).filter(BookInventory.book_id == book_id).first()
        if not inventory:
            return None  # 如果没有找到库存信息，返回 None
        
        # 使用事务管理器，确保库存更新是原子操作
        with transaction(self.db):  # 使用上下文管理器确保事务原子性
            # 更新库存数量
            if inventory_data.quantity is not None:
                inventory.quantity = inventory_data.quantity

        self.db.refresh(inventory)

        return BookInventoryOut.model_validate(inventory).model_dump()  # 返回更新后的库存信息

    # 删除图书库存信息
    def delete_inventory(self, book_id: int) -> None:
        # 查找库存记录
        inventory = self.db.query(BookInventory).filter(BookInventory.book_id == book_id).first()
        if not inventory:
            raise ValueError(f"Inventory for book_id {book_id} not found.")  # 如果没有找到库存记录，抛出异常

        with transaction(self.db):
            self.db.delete(inventory)   # 删除库存记录
        
        return BookInventoryOut.model_validate(inventory).model_dump()  # 返回更新后的库存信息
