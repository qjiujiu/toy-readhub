# 借阅订单, 需要拥有一个唯一单号，当用户归还之后会产生归还单号
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

# 可选：在应用层用 Enum 来校验和限制状态值（不直接映射数据库 Enum）
from enum import Enum

class OrderStatus(str, Enum):
    borrowed = "borrowed"
    returned = "returned"
    lost = "lost"


class Order(Base):
    """ 借阅订单 ORM 模型，对应 MySQL 之中的 Orders 表：

    CREATE TABLE IF NOT EXISTS Orders (
        order_id VARCHAR(64) PRIMARY KEY,        		     -- 借阅单号（可以用 UUID 或系统生成编码）
        user_id INT NOT NULL,                     			 -- 借阅人 ID（可关联用户系统）
        book_id INT NOT NULL,                     			 -- 借阅书籍
        warehouse_name VARCHAR(100) NOT NULL,     			 -- 所借书所在图书馆/仓库
        status VARCHAR(20) NOT NULL DEFAULT 'borrowed',      -- 借阅状态
        borrow_time DATETIME NOT NULL,           			 -- 借出时间
        return_time DATETIME,                    		     -- 归还时间（可为空）

    );

    ALTER TABLE Orders
    ADD CONSTRAINT fk_orders_book_id
    FOREIGN KEY (book_id) REFERENCES Books(bid);

    ALTER TABLE Orders
    ADD CONSTRAINT fk_orders_user_id
    FOREIGN KEY (user_id) REFERENCES Users(uid);

    """
    __tablename__ = "orders"

    # 借阅订单号（UUID 或序列）
    order_id = Column(String(64), primary_key=True)            
    
    # 用户 ID
    user_id = Column(Integer, ForeignKey("users.uid"),  nullable=False)
    
    # 图书 ID
    book_id = Column(Integer, ForeignKey("books.bid"), nullable=False)
    
    # 所借书所在图书馆/仓库
    warehouse_name = Column(String(100), nullable=False)       

    # 用 VARCHAR 存储状态，默认 'borrowed'
    status = Column(String(20), nullable=False, default="borrowed")  

    borrow_time = Column(DateTime, default=datetime.utcnow, nullable=False)  # 借书时间
    return_time = Column(DateTime, nullable=True)               # 归还时间（可为空）

    
    # 关联到 Book 和 User
    book = relationship("Book", back_populates="orders")
    user = relationship("User", back_populates="orders")