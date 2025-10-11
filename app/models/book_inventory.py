from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base

class BookInventory(Base):
    """ 图书库存模型，用于记录每本图书在每个图书馆（或仓库）中的库存数量。

        CREATE TABLE book_inventory (
            inv_id INT PRIMARY KEY AUTO_INCREMENT,
            book_id INT NOT NULL,
            warehouse_name VARCHAR(100) NOT NULL,
            quantity INT NOT NULL DEFAULT 0,
            FOREIGN KEY (book_id) REFERENCES books(bid),
            UNIQUE KEY unique_book_warehouse (book_id, warehouse_name)
        );
    """
    __tablename__ = "book_inventory"

    inv_id = Column(Integer, primary_key=True, autoincrement=True)      # 主键 ID
    book_id = Column(Integer, ForeignKey("books.bid"), nullable=False)  # 外键，关联到 books 表
    warehouse_name = Column(String(100), nullable=False)                # 仓库名称，校园场景之中，i.e. 图书馆名称
    quantity = Column(Integer, nullable=False, default=0)               # 当前库存数量

    # 约束一个图书 (book_id) 只在某个仓库 (warehouse_name) 之中最多出现一条记录
    __table_args__ = (
        UniqueConstraint("book_id", "warehouse_name", name="unique_book_warehouse"),
    )

    # ORM 关联：相当于一个反向引用，能从图书找到与之管理的仓库
    book = relationship("Book", backref="inventories")