from app.models.base import Base
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relationship

class BookLocation(Base):
    """ 图书存放位置表模型（实体书维度；同馆同 book_id 仅一条位置记录）。
    
        CREATE TABLE IF NOT EXISTS book_locations (
            loc_id INT PRIMARY KEY AUTO_INCREMENT,
            book_id INT NOT NULL,
            isbn VARCHAR(20) NOT NULL,
            area VARCHAR(50),
            floor VARCHAR(50),
            warehouse_name VARCHAR(100) NOT NULL,

            -- 为查询效率添加索引
            INDEX idx_book_id (book_id),
            INDEX idx_isbn (isbn),

            -- 关键唯一约束：同馆同 book_id 仅一条位置记录
            UNIQUE KEY uk_location_bookid_wh (book_id, warehouse_name),

            -- 关联 books(bid)（实体书标识）
            CONSTRAINT fk_book_locations_bookid
              FOREIGN KEY (book_id) REFERENCES books (bid)
              ON UPDATE CASCADE ON DELETE CASCADE,

            -- 关联 books(isbn)（品种）
            -- 注意：父表 books.isbn 需有普通索引（非唯一）
            -- e.g. ALTER TABLE books ADD INDEX idx_books_isbn (isbn);
            CONSTRAINT fk_book_locations_isbn
              FOREIGN KEY (isbn) REFERENCES books (isbn)
              ON UPDATE CASCADE ON DELETE CASCADE,

            -- 复合外键：位置记录必须对应一条库存记录（isbn, warehouse_name）
            CONSTRAINT fk_location_inventory
              FOREIGN KEY (isbn, warehouse_name)
              REFERENCES book_inventory (isbn, warehouse_name)
              ON UPDATE CASCADE ON DELETE CASCADE
        );
    """
    __tablename__ = "book_locations"

    loc_id = Column(Integer, primary_key=True, autoincrement=True)                     # 主键 ID
    book_id = Column(Integer, ForeignKey("books.bid"), nullable=False, index=True)     # 外键 → books.bid（实体书）
    isbn = Column(String(20), ForeignKey("books.isbn"), nullable=False, index=True)    # 外键 → books.isbn（品种）
    area = Column(String(50), nullable=True)                                           # 所在区域（如 A-Z 区）
    floor = Column(String(50), nullable=True)                                          # 所在楼层（如 1F, 2F）
    warehouse_name = Column(String(100), nullable=False)                               # 仓库/馆名

    __table_args__ = (
        # 同馆同 book_id 仅一条位置记录
        UniqueConstraint("book_id", "warehouse_name", name="uk_location_bookid_wh"),

        # 复合外键：与库存 (isbn, warehouse_name) 对应（BookInventory : BookLocation = 1 : N）
        ForeignKeyConstraint(
            ["isbn", "warehouse_name"],
            ["book_inventory.isbn", "book_inventory.warehouse_name"],
            name="fk_location_inventory",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )

    # ORM 关系
    book = relationship("Book", back_populates="locations", foreign_keys=[book_id])  # 多对一：位置 → 实体书
    inventory = relationship("BookInventory", back_populates="locations")            # 多对一：位置 → 库存（同 isbn+馆）