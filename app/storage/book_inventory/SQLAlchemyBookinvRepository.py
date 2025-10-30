from sqlalchemy.orm import Session
from app.models.book_inventory import BookInventory  # 图书库存模型
from app.schemas.book_inventory import BookInventoryCreate, BookInventoryUpdate, BookInventoryOut
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from typing import Optional, Dict, List
from app.core.db import transaction
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import selectinload
from app.core.logx import logger
class SQLAlchemyBookinvRepository(IBookInventoryRepository):
    def __init__(self, db: Session):
        self.db = db  # 数据库会话对象
    
    # 根据图书ID获取图书库存信息
    def get_inventories_by_bid(self, book_id: int) -> List[dict]:
        invs = (
            self.db.query(BookInventory)
            .filter(BookInventory.book_id == book_id)
            .order_by(BookInventory.warehouse_name.asc())  # 可选：按校区名排序
            .all()
        )
        return [BookInventoryOut.model_validate(inv).model_dump() for inv in invs]

    # 根据图书ID和校区信息获取图书记录
    def get_by_bid_and_warehouse(self, book_id: int, warehouse_name: str) -> Optional[dict]:
        name = (warehouse_name or "").strip()
        inv = (
            self.db.query(BookInventory)
            .filter(BookInventory.book_id == book_id, BookInventory.warehouse_name == name)
            .one_or_none()
        )
        if not inv:
            return None
        return BookInventoryOut.model_validate(inv).model_dump()


    # 根据图书ID和仓库名称增加库存数量（默认 +1）
    def update_inventory(self, book_id: int, warehouse_name: str, delta: int = 1) -> Optional[dict]:
        inv = (
            self.db.query(BookInventory)
            .filter(BookInventory.book_id == book_id, BookInventory.warehouse_name == warehouse_name.strip())
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
    def create_inventory(self, inventory_data: BookInventoryCreate) -> Dict:
        inv = BookInventory(book_id=inventory_data.book_id, warehouse_name=inventory_data.warehouse_name, quantity=1)
        with transaction(self.db):
            self.db.add(inv)
        # 确保关系可用（当前会话中 inv.book 会被懒加载；为安全也可 selectinload 重新查一次）
        self.db.refresh(inv)
        _ = inv.book  # 触发加载（若未加载）
        return BookInventoryOut.model_validate(inv).model_dump()
    
    

    # 批量删除库存：按书 ID（返回删除条数）
    def delete_all_by_book_id(self, book_id: int) -> int:
        rows = self.db.query(BookInventory).filter(BookInventory.book_id == book_id).all()
        if not rows:
            return 0
        count = len(rows)
        with transaction(self.db):
            for r in rows:
                self.db.delete(r)
        return count
    
    
    # 业务层删除图书时，只需要调用批量删除库存的方法
    # # 删除图书库存信息，
    # def delete_inventory(self, book_id: int) -> None:
    #     # 查找库存记录
    #     inventory = self.db.query(BookInventory).filter(BookInventory.book_id == book_id).first()
    #     if not inventory:
    #         raise ValueError(f"Inventory for book_id {book_id} not found.")  # 如果没有找到库存记录，抛出异常

    #     with transaction(self.db):
    #         self.db.delete(inventory)   # 删除库存记录
        
    #     return BookInventoryOut.model_validate(inventory).model_dump()  # 返回更新后的库存信息
    
    
