from app.models.base import Base
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relationship

class BookLocation(Base):
    """ 图书存放位置表模型。
    
        CREATE TABLE IF NOT EXISTS book_locations (
            loc_id INT PRIMARY KEY AUTO_INCREMENT,
            book_id INT NOT NULL,
            area VARCHAR(50),
            floor VARCHAR(50),
            warehouse_name VARCHAR(100) NOT NULL,

            -- 为查询效率添加索引
            INDEX idx_book_id (book_id),

            -- 保证“一本书在同一馆只保留一条位置”
            UNIQUE KEY uk_location_book_wh (book_id, warehouse_name),

            -- 关联 books(bid)
            CONSTRAINT fk_book_locations_book
              FOREIGN KEY (book_id) REFERENCES books (bid)
              ON UPDATE CASCADE ON DELETE CASCADE,

            -- 复合外键：位置记录必须对应一条库存记录（book_id, warehouse_name）
            CONSTRAINT fk_location_inventory
              FOREIGN KEY (book_id, warehouse_name)
              REFERENCES book_inventory (book_id, warehouse_name)
              ON UPDATE CASCADE ON DELETE CASCADE
        );
    """
    
    __tablename__ = "book_locations"

    loc_id = Column(Integer, primary_key=True, autoincrement=True)                   # 主键 ID
    book_id = Column(Integer, ForeignKey("books.bid"), nullable=False, index=True)   # 外键 → books
    area = Column(String(50), nullable=True)                                         # 所在区域（如 A-Z 区）
    floor = Column(String(50), nullable=True)                                        # 所在楼层（如 1F, 2F）
    warehouse_name = Column(String(100), nullable=False)                             # 仓库/馆名

    # 复合唯一：一本书在同一馆仅一条位置记录
    __table_args__ = (
        UniqueConstraint("book_id", "warehouse_name", name="uk_location_book_wh"),
        ForeignKeyConstraint(
            ["book_id", "warehouse_name"],
            ["book_inventory.book_id", "book_inventory.warehouse_name"],
            name="fk_location_inventory",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )

    # 关系
    book = relationship("Book", back_populates="locations")
    # 一对一：与库存通过 (book_id, warehouse_name) 关联
    inventory = relationship("BookInventory", back_populates="location", uselist=False)    # uselist=False 一对一