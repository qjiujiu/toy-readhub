from sqlalchemy.orm import Session
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate, BookOut, BatchBooksOut
from app.storage.book.book_interface import IBookRepository
from typing import Optional, List, Dict, Union
from contextlib import contextmanager
import logging
from app.core.db import transaction


class SQLAlchemyBookRepository(IBookRepository):
    def __init__(self, db: Session):
        self.db = db

    # 批量查询图书（可分页）
    def get_batch_books(self, page: int, page_size: int) -> BatchBooksOut:
        skip = page * page_size
        books = self.db.query(Book).offset(skip).limit(page_size).all()
        total = self.db.query(Book).count()
        return BatchBooksOut(total=total, count=len(books), books=books).model_dump()

    # 根据主键 bid 获取图书
    def get_book_by_bid(self, bid: int) -> Optional[BookOut]:
        book = self.db.query(Book).filter(Book.bid == bid).first()
        if not book:
            return None
        return BookOut.model_validate(book).model_dump()

    # 根据 ISBN 获取图书
    def get_book_by_isbn(self, isbn: str) -> Optional[BookOut]:
        book = self.db.query(Book).filter(Book.isbn == isbn).first()
        if not book:
            return None
        return BookOut.model_validate(book).model_dump()

    # 根据书名获取图书（可能有多本书同名）
    def get_books_by_title(self, title: str) -> List[BookOut]:
        books = self.db.query(Book).filter(Book.title == title).all()
        return [BookOut.model_validate(book).model_dump() for book in books]

    # 根据作者获取图书（可能有多本书同一作者）
    def get_books_by_author(self, author: str) -> List[BookOut]:
        books = self.db.query(Book).filter(Book.author == author).all()
        return [BookOut.model_validate(book).model_dump() for book in books]

    # 批量创建图书
    def create_batch_books(self, books: List[BookCreate]) -> BatchBooksOut:
        book_orms = [Book(**b.dict()) for b in books]
        
        with transaction(self.db):  # 使用事务管理器
            self.db.add_all(book_orms)  # 批量添加图书
        
        # 刷新每个图书以便获取自增主键等
        for book in book_orms:
            self.db.refresh(book)
        
        return BatchBooksOut(total=len(book_orms), count=len(book_orms), books=book_orms).model_dump()

    # 创建单本图书
    def create_book(self, book_data: BookCreate) -> BookOut:
        book = Book(**book_data.dict())

        with transaction(self.db):  # 使用事务管理器
            self.db.add(book)  # 添加图书
        self.db.refresh(book)
        return BookOut.model_validate(book).model_dump()

    # 更新图书信息（通过 ISBN）
    def update_book_by_isbn(self, isbn: str, book_data: BookUpdate) -> Optional[BookOut]:
        book = self.db.query(Book).filter(Book.isbn == isbn).first()
        if not book:
            return None
        
        with transaction(self.db):  # 使用事务管理器
            # 更新图书的字段
            for field, value in book_data.dict(exclude_unset=True).items():
                setattr(book, field, value)

        self.db.refresh(book)
        return BookOut.model_validate(book).model_dump()

    # 删除图书（通过 ISBN）
    def delete_book_by_isbn(self, isbn: str) -> None:
        book = self.db.query(Book).filter(Book.isbn == isbn).first()
        if not book:
            raise ValueError(f"Book with ISBN {isbn} not found.")
        
        with transaction(self.db):  # 使用事务管理器
            self.db.delete(book)  # 删除图书
        
        return BookOut.model_validate(book).model_dump()
        
