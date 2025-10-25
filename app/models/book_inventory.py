from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base

class BookInventory(Base):
    """ 图书库存模型，用于记录每本图书在每个图书馆（或仓库）中的库存数量。

        CREATE TABLE IF NOT EXISTS book_inventory (
            inv_id INT PRIMARY KEY AUTO_INCREMENT,
            book_id INT NOT NULL,
            warehouse_name VARCHAR(100) NOT NULL,
            quantity INT NOT NULL DEFAULT 0,

            -- 关联 books(bid)
            CONSTRAINT fk_book_inventory_book
              FOREIGN KEY (book_id) REFERENCES books(bid),

            -- 唯一：一本书在同一馆仅一条库存记录
            UNIQUE KEY unique_book_warehouse (book_id, warehouse_name)
        );
    """
    __tablename__ = "book_inventory"

    inv_id = Column(Integer, primary_key=True, autoincrement=True)       # 主键 ID
    book_id = Column(Integer, ForeignKey("books.bid"), nullable=False)   # 外键 → books
    warehouse_name = Column(String(100), nullable=False)                 # 仓库/馆名
    quantity = Column(Integer, nullable=False, default=0)                # 库存数量

    __table_args__ = (
        UniqueConstraint("book_id", "warehouse_name", name="unique_book_warehouse"),
    )

    # ORM 关联：相当于一个反向引用，能从图书找到与之管理的仓库
    book = relationship("Book", backref="inventories")

    # 一对一回指：通过 (book_id, warehouse_name) 关联到唯一的位置（若存在）
    location = relationship("BookLocation", back_populates="inventory", uselist=False)