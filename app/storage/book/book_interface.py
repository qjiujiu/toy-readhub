from typing import Protocol, Optional, List
from app.schemas.book import BookCreate, BookUpdate, BookOut
from app.schemas.book import BatchBooksOut

class IBookRepository(Protocol):
    # 批量查询图书（可分页）
    def get_batch_books(self, page: int, page_size: int) -> BatchBooksOut:
        ...

    # 根据主键 bid 获取图书
    def get_book_by_bid(self, bid: int) -> Optional[BookOut]:
        ...

    # 根据 ISBN 获取图书
    def get_book_by_isbn(self, isbn: str) -> Optional[BookOut]:
        ...

    # 根据书名获取图书（可能有多本书同名）
    def get_books_by_title(self, title: str) -> List[BookOut]:
        ...

    # 根据作者获取图书（可能有多本书同一作者）
    def get_books_by_author(self, author: str) -> List[BookOut]:
        ...

    # 批量创建图书
    def create_batch_books(self, books: List[BookCreate]) -> BatchBooksOut:
        ...

    # 创建单本图书
    def create_book(self, book_data: BookCreate) -> BookOut:
        ...

    # 更新图书信息（通过 ISBN）
    def update_book_by_isbn(self, isbn: str, book_data: BookUpdate) -> Optional[BookOut]:
        ...

    # 删除图书（通过 ISBN）
    def delete_book_by_isbn(self, isbn: str) -> None:
        ...
