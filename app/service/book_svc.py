from typing import Optional, Dict, List
from app.schemas.book import (
    BookCreate,
    BookUpdate,
    BookOut,
    BatchBooksOut
)
from app.storage.book.book_interface import IBookRepository  
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from app.schemas.book_inventory import (
    BookInventoryCreate
)
from app.models.book import TagCategory

# 批量查询图书（可分页）
def get_batch_books(repo: IBookRepository, page: int = 0, page_size: int = 10) -> Dict:
    batch_books = repo.get_batch_books(page, page_size)
    # 对返回的每本书，转换tags为类别名称
    for book in batch_books['books']:
        book['tags'] = TagCategory.to_name(book['tags'])
    return batch_books


# 根据主键 bid 获取图书
def get_book_by_bid(repo: IBookRepository, bid: int, to_dict: bool = True) -> Optional[Dict]:
    book = repo.get_book_by_bid(bid)
    if not book:
        return None
    book['tags'] = TagCategory.to_name(book['tags'])
    return book


# 根据 ISBN 获取图书
def get_book_by_isbn(repo: IBookRepository, isbn: str, to_dict: bool = True) -> Optional[Dict]:
    book = repo.get_book_by_isbn(isbn)
    if not book:
        return None
    # 将字母转换为类别名称
    book['tags'] = TagCategory.to_name(book['tags'])
    return book


# 根据书名获取图书（可能有多本书同名）
def get_books_by_title(repo: IBookRepository, title: str) -> List[Dict]:
    books = repo.get_books_by_title(title)
    for book in books['books']:
        book['tags'] = TagCategory.to_name(book['tags'])
    return books


# 根据作者获取图书（可能有多本书同一作者）
def get_books_by_author(repo: IBookRepository, author: str) -> List[Dict]:
    books = repo.get_books_by_author(author)
    for book in books['books']:
        book['tags'] = TagCategory.to_name(book['tags'])
    return books


# 批量创建图书
def create_batch_books(repo: IBookRepository, books: List[BookCreate]) -> Dict:
    batch_books = repo.create_batch_books(books)
    return batch_books


# 创建单本图书
# def create_book(repo: IBookRepository, book_data: BookCreate) -> Dict:
#     # 校验tags字段是否为合法字母
#     if book_data.tags:
#         try:
#             TagCategory.validate_tag(book_data.tags)  # 校验tag是否合法（只校验字母）
#         except ValueError as e:
#             raise ValueError(f"Invalid tag: {str(e)}")

#     # 调用数据层创建图书
#     new_book = repo.create_book(book_data)
#     return new_book


def create_book(book_repo: IBookRepository, inv_repo: IBookInventoryRepository, book_data: BookCreate) -> Dict:  # 返回的是 BookInventoryOut 的 dict
    print(book_data)
    # 1) 校验 tags
    if book_data.tags:
        try:
            book_data.tags = TagCategory.validate_tag(book_data.tags)
        except ValueError as e:
            raise ValueError(f"Invalid tag: {e}")

    # 2) 校验库存必要信息：warehouse_name
    if not book_data.warehouse_name or not book_data.warehouse_name.strip():
        raise ValueError("warehouse_name is required for inventory")
    warehouse_name = book_data.warehouse_name.strip()

    # 3) 查是否已存在同 ISBN 的图书
    existing_book = book_repo.get_book_by_isbn(book_data.isbn)  # None 或 BookOut 的 dict
    if existing_book:
        book_id = existing_book["bid"]

        # 3.1 查该仓库是否已有库存
        inv = inv_repo.get_by_bid_and_warehouse(book_id=book_id, warehouse_name=warehouse_name)
        if inv:
            # 3.2 已有库存 → 数量 +1，并返回更新后的库存（含 book 嵌套）
            updated = inv_repo.increment_quantity(book_id=book_id, warehouse_name=warehouse_name, delta=1)
            # increment_quantity 按我们实现会返回更新后的 BookInventoryOut；若返回 None（极少见并发），兜底再查一次
            return updated or inv_repo.get_by_book_and_warehouse(book_id=book_id, warehouse_name=warehouse_name)
        else:
            # 3.3 无库存 → 新建库存 quantity=1，并返回（含 book 嵌套）
            created = inv_repo.create_inventory(
                BookInventoryCreate(book_id=book_id, warehouse_name=warehouse_name)
            )
            return created

    # 4) 不存在图书：先插 books，再插库存，并返回 BookInventoryOut
    payload = book_data.model_dump()
    payload.pop("warehouse_name", None)  # 删掉不属于 Book 的字段
    created_book = book_repo.create_book(BookCreate(**payload))
    book_id = created_book["bid"]

    created_inv = inv_repo.create_inventory(
        BookInventoryCreate(book_id=book_id, warehouse_name=warehouse_name)
    )
    return created_inv


# 更新图书信息（通过 ISBN）
def update_book_by_isbn(repo: IBookRepository, isbn: str, book_data: BookUpdate) -> Optional[Dict]:
    updated_book = repo.update_book_by_isbn(isbn, book_data)
    if not updated_book:
        return None
    return updated_book


# 删除图书（通过 ISBN）
def delete_book_by_isbn(repo: IBookRepository, isbn: str) -> None:
    book_info = repo.delete_book_by_isbn(isbn)
    return book_info
