# 借阅订单, 需要拥有一个唯一单号，当用户归还之后会产生归还单号
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, validates
from app.models.base import Base
from datetime import datetime, timedelta



class Order(Base):
    """ 借阅订单 ORM 模型，对应 MySQL 之中的 orders 表：

    CREATE TABLE IF NOT EXISTS orders (
        order_id INT AUTO_INCREMENT PRIMARY KEY,             -- 借阅单号（可以用 UUID 或系统生成编码）
        user_id INT NOT NULL,                     			 -- 借阅人 ID（可关联用户系统）
        book_id INT NOT NULL,                     			 -- 借阅书籍
        warehouse_name VARCHAR(100) NOT NULL,     			 -- 所借书所在图书馆/仓库
        status VARCHAR(20) NOT NULL DEFAULT 'borrowed',      -- 借阅状态
        borrow_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 自动填充当前时间
        return_time DATETIME                    		     -- 归还时间（可为空）
    );

    ALTER TABLE orders
    ADD CONSTRAINT fk_orders_book_id
    FOREIGN KEY (book_id) REFERENCES Books(bid);

    ALTER TABLE orders
    ADD CONSTRAINT fk_orders_user_id
    FOREIGN KEY (user_id) REFERENCES Users(uid);

    """
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True,  autoincrement=True)                         # 借阅订单号（UUID 或序列）            
    user_id = Column(Integer, ForeignKey("users.uid"),  nullable=False)     # 用户 ID
    book_id = Column(Integer, ForeignKey("books.bid"), nullable=False)      # 图书 ID
    warehouse_name = Column(String(100), nullable=False)                    # 所借书所在图书馆/仓库
    status = Column(String(20), nullable=False, default="borrowed")         # 用 VARCHAR 存储状态，默认 'borrowed'

    borrow_time = Column(DateTime, nullable=False, server_default=func.now())  # 借书时间
    return_time = Column(DateTime, nullable=True)                              # 归还时间（可为空）
    
    # 关联到 Book 和 User
    book = relationship("Book", back_populates="orders")
    user = relationship("User", back_populates="orders")

    def calculate_return_time(self, borrow_time: datetime, borrow_duration_seconds: int = 30) -> datetime:
        """计算还书时间，借书时间 + 借书时长（默认为30秒）。"""
        # 使用传入的 borrow_time 计算 return_time
        return borrow_time + timedelta(seconds=borrow_duration_seconds)