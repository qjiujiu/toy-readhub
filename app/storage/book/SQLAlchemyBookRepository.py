from sqlalchemy.orm import Session
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate, BookOut, BatchBooksOut, BookOnlyCreate, BookDetailOut
from app.storage.book.book_interface import IBookRepository
from typing import Optional, List
from app.core.logx import logger
from app.core.db import transaction


class SQLAlchemyBookRepository(IBookRepository):
    def __init__(self, db: Session):
        self.db = db

    # 批量查询图书（可分页）
    def get_batch_books(self, page: int, page_size: int) -> BatchBooksOut:
        skip = page * page_size
        books = self.db.query(Book).offset(skip).limit(page_size).all()
        total = self.db.query(Book).count()
        return BatchBooksOut(total=total, count=len(books), book=books).model_dump()

    # 根据主键 bid 获取图书
    def get_book_by_bid(self, bid: int) -> Optional[BookOut]:
        book = self.db.query(Book).filter(Book.bid == bid).first()
        if not book:
            return None
        return BookOut.model_validate(book).model_dump()

    # 根据 ISBN 获取图书
    def get_book_by_isbn(self, isbn: str) -> BatchBooksOut:
        books = self.db.query(Book).filter(Book.isbn == isbn).all()
        total = self.db.query(Book).filter(Book.isbn == isbn).count()
        if not books:
            return None
        return BatchBooksOut(total=total, count=len(books), book=books)

    # 根据书名获取图书（可能有多本书同名）
    def get_books_by_title(self, title: str) -> List[BookOut]:
        books = self.db.query(Book).filter(Book.title == title).all()
        return [BookOut.model_validate(book).model_dump() for book in books]

    # 根据作者获取图书（可能有多本书同一作者）
    def get_books_by_author(self, author: str) -> List[BookOut]:
        books = self.db.query(Book).filter(Book.author == author).all()
        return [BookOut.model_validate(book).model_dump() for book in books]

    # 根据作者和书名联立查找图书
    def get_books_by_author_and_title(self, author: str, title: str) -> List[BookOut]:
        # 使用 filter() 根据作者和书名进行联立查询
        books = self.db.query(Book).filter(Book.author == author, Book.title == title).all()
        # 将查询结果转换为 BookOut 模型的字典列表
        return [BookOut.model_validate(book).model_dump() for book in books]

    # 创建单本图书
    def create_book(self, book_data: BookOnlyCreate) -> BookOut:
        book = Book(**book_data.model_dump())

        with transaction(self.db):  # 使用事务管理器
            self.db.add(book)  # 添加图书
        self.db.refresh(book)
        return BookOut.model_validate(book)

    # 更新图书基本信息（通过 bid）
    def update_book_info(self, bid: int, book_data: BookUpdate) -> Optional[BookOut]:
        book = self.db.query(Book).filter(Book.bid == bid).first()
        if not book:
            raise ValueError(f"Book with bid {bid} not found.")
        
        with transaction(self.db):  # 使用事务管理器
            # 更新图书的字段
            for field, value in book_data.dict(exclude_unset=True).items():
                setattr(book, field, value)

        self.db.refresh(book)
        return BookOut.model_validate(book).model_dump()

    # 删除图书（通过 bid）
    def delete_book_by_bid(self, bid: int) -> None:
        book = self.db.query(Book).filter(Book.bid == bid).first()
        logger.debug(book)
        if not book:
            raise ValueError(f"Book with bid {bid} not found.")
        
        with transaction(self.db):  # 使用事务管理器
            self.db.delete(book)  # 删除图书
        return BookOut.model_validate(book).model_dump()
        
