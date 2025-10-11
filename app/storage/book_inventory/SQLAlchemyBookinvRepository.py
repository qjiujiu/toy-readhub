from sqlalchemy.orm import Session
from app.models.book_inventory import BookInventory  # 图书库存模型
from app.schemas.book_inventory import BookInventoryCreate, BookInventoryUpdate, BookInventoryOut
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from typing import Optional, Dict, List
from contextlib import contextmanager
import logging

# 使用 Python上下文管理器来处理数据库事务, 在失败的时候自动回滚, 通过事务管理器来保证原子性
# 成功时提交事务(commit),  commit 完成之后才能调用 refresh 获取最新状态;  失败时回滚事务, 打印异常调用栈，并且重新向上抛出异常!
@contextmanager
def transaction(db: Session):
    try:
        yield db
        db.commit()  # 提交事务
    except Exception as e:
        logging.exception(e)
        db.rollback()  # 回滚事务
        raise

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

    # 添加一本图书的库存信息，初始库存为 1
    def create_inventory(self, inventory_data: BookInventoryCreate) -> BookInventoryOut:
        # 创建新的图书库存对象，并设置库存初始值为 1
        inventory = BookInventory(
            book_id=inventory_data.book_id,
            warehouse_name=inventory_data.warehouse_name,
            quantity=1  # 初始库存为 1
        )

        # 使用事务管理器来将添加新用户到数据库
        with transaction(self.db):
            self.db.add(inventory)

        self.db.refresh(inventory)  # 刷新以确保获取到数据库中生成的 ID 等信息

        return BookInventoryOut.model_validate(inventory).model_dump()  # 返回新创建的库存信息

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
