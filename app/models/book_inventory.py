from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from .base import Base

class BookInventory(Base):
    """ 图书库存模型：每个馆（仓库）中某个 ISBN 的库存数量。
    
        CREATE TABLE IF NOT EXISTS book_inventory (
            inv_id INT PRIMARY KEY AUTO_INCREMENT,
            isbn VARCHAR(20) NOT NULL,
            warehouse_name VARCHAR(100) NOT NULL,
            quantity INT NOT NULL DEFAULT 0,

            -- 不再与 books 建立外键；由应用层保证 isbn 的合法性
            -- 为查询效率添加普通索引
            INDEX idx_inv_isbn (isbn),

            -- 每馆每 ISBN 仅一条库存记录
            UNIQUE KEY unique_book_warehouse (isbn, warehouse_name)
        );
    """
    __tablename__ = "book_inventory"

    inv_id = Column(Integer, primary_key=True, autoincrement=True)      # 主键 ID
    # 取消 ForeignKey("books.isbn") —— 仅普通列与索引，由应用层保证一致性
    isbn = Column(String(20), nullable=False, index=True)               # ISBN（普通索引）
    warehouse_name = Column(String(100), nullable=False)                # 仓库/馆名
    quantity = Column(Integer, nullable=False, default=0)               # 库存数量

    __table_args__ = (
        UniqueConstraint("isbn", "warehouse_name", name="unique_book_warehouse"),
    )

    # 关系：一个库存记录，对应多条位置记录（同馆同 ISBN 下的多册实体书）
    locations = relationship("BookLocation", back_populates="inventory")