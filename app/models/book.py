from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base
from typing import List, Dict, Any
from enum import Enum

# TODO TagCategory类应该挪到 book_location 模型中
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
    
    @classmethod
    def translate_tags(cls, data: List[Dict], nested: bool = True) -> List[Dict]:
        """
        将图书 tags 从字母转换为中文类别名。

        :param data: List[dict]
            - 若 nested=True，输入形如 [{"book": {"tags": "F"}}, ...]
            - 若 nested=False，输入形如 [{"tags": "F"}, ...]
        :param nested: bool，是否 tags 在 book 字段中（默认 True）
        :return: List[dict] 转换后的数据
        """
        for item in data:
            try:
                if nested:  # 第一种形式：tags 在 book 中
                    book = item.get("book")
                    if book and book.get("tags"):
                        book["tags"] = cls.to_name(book["tags"])
                else:       # 第二种形式：tags 在 item 顶层
                    if item.get("tags"):
                        item["tags"] = cls.to_name(item["tags"])
            except Exception:
                # 出错时忽略（可选：logger.warning）
                continue
        return data

class Book(Base):
    """ 图书数据库模型，用于表示每本书的基本信息。
    
        CREATE TABLE IF NOT EXISTS books (
            bid INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            isbn VARCHAR(20) NOT NULL UNIQUE,
            abstract TEXT,
            tags VARCHAR(255)
        );
    """
    __tablename__ = "books"

    bid = Column(Integer, primary_key=True, autoincrement=True)  # 图书 ID，主键，自增
    title = Column(String(255), nullable=False)                  # 书名（必填）
    author = Column(String(255), nullable=False)                 # 作者（必填）
    isbn = Column(String(20), unique=True, nullable=False)       # 国际标准书号，唯一（必填）
    abstract = Column(Text, nullable=True)                       # 图书简介（可为空）

    tags = Column(String(255), nullable=True)                    # 图书标签（多个标签用逗号分隔，例如：文学,历史,科幻）

    orders = relationship("Order", back_populates="book")
    locations = relationship("BookLocation", back_populates="book", cascade="all, delete-orphan")
    # cascade="all, delete-orphan" 删除 Book 时，自动删除其关联的 BookLocation。