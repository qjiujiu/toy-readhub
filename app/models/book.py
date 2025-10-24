from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base
from typing import List, Dict, Any
from enum import Enum

class TagCategory(Enum):
    A = "马克思、列宁、毛泽东、邓小平理论"
    B = "哲学、宗教"
    C = "社会科学总论"
    D = "政治、法律"
    E = "军事"
    F = "经济"
    G = "文化、科学、教育、体育"
    H = "语言、文字"
    I = "文学"
    J = "艺术"
    K = "历史、地理"
    N = "自然科学总论"
    O = "数理科学和化学"
    P = "天文学、地球科学"
    Q = "生物科学"
    R = "医药、卫生"
    S = "农业科学"
    T = "工业技术"
    U = "交通运输"
    V = "航空、航天"
    X = "环境科学、安全科学"
    Z = "综合性图书"

    # 校验tags是否在Enum中
    @classmethod
    def validate_tag(cls, tag: str):
        if tag not in cls.__members__:
            raise ValueError(f"Invalid tag: {tag} is not a valid category.")
    # 把字母转成中文类别名
    @classmethod
    def to_name(cls, tag: str) -> str:
        cls.validate_tag(tag)
        return cls[tag].value
    
    #  遍历库存记录列表，将其中每个 book 的 tags 从字母转为中文类别名
    @classmethod
    def translate_books(cls, books: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        param books: List[dict]，每个元素形如 {"book": {"tags": "F", ...}, ...}
        return: List[dict]，修改后的 books 列表
        """
        for item in books:
            book = item.get("book")
            if book and book.get("tags"):
                try:
                    book["tags"] = cls.to_name(book["tags"])
                except Exception as e:
                    # 出现非法标签或异常时，可选择忽略或打印日志
                    pass
        return books

class Book(Base):
    """ 图书数据库模型，用于表示每本书的基本信息、库存量以及所在区域等信息。
    
        CREATE TABLE IF NOT EXISTS books (
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

    bid = Column(Integer, primary_key=True, autoincrement=True)  # 图书 ID，主键，自增
    title = Column(String(255), nullable=False)               # 书名（必填）
    author = Column(String(255), nullable=False)              # 作者（必填）
    isbn = Column(String(20), unique=True, nullable=False)   # 国际标准书号，唯一（必填）
    abstract = Column(Text, nullable=True)             # 图书简介（可为空）

    area = Column(String(50), nullable=True)                 # 所在区域（如 A-Z 区）
    floor = Column(String(50), nullable=True)                # 所在楼层（如 1F, 2F）

    tags = Column(String(255), nullable=True)                 # 图书标签（多个标签用逗号分隔，例如：文学,历史,科幻）


    orders = relationship("Order", back_populates="book")
    