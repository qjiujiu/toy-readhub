from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class Book(Base):
    """ 图书数据库模型，用于表示每本书的基本信息、库存量以及所在区域等信息。
    
        CREATE TABLE IF NOT EXISTS Books (
            bid INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            isbn VARCHAR(20) NOT NULL UNIQUE,
            abstract TEXT,
            area VARCHAR(50),
            floor VARCHAR(50),
            tags VARCHAR(255)
        );

    """
    __tablename__ = "books"

    bid = Column(Integer, primary_key=True, index=True)  # 图书 ID，主键，自增
    title = Column(String, nullable=False)               # 书名（必填）
    author = Column(String, nullable=False)              # 作者（必填）
    isbn = Column(String, unique=True, nullable=False)   # 国际标准书号，唯一（必填）
    abstract = Column(String, nullable=True)             # 图书简介（可为空）

    area = Column(String, nullable=True)                 # 所在区域（如 A-Z 区）
    floor = Column(String, nullable=True)                # 所在楼层（如 1F, 2F）

    tags = Column(String, nullable=True)                 # 图书标签（多个标签用逗号分隔，例如：文学,历史,科幻）


    orders = relationship("Order", back_populates="book")
    