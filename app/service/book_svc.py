from typing import Optional, Dict, List, Any
from app.schemas.book import (
    BookCreate,
    BookUpdate,
    BookOnlyCreate,
    BookOut,
    BatchBooksOut
)
from app.storage.book.book_interface import IBookRepository  
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from app.schemas.book_inventory import (
    BookInventoryCreate
)
from app.models.book import TagCategory
from app.core.logx import logger

logger.is_debug(True)


"""
读取图书功能：
- 根据图书主键 bid 获取图书信息包含该图书的库存信息（BookInventoryOut）
- 根据图书 ISBN 获取图书信息包含该图书的库存信息（BookInventoryOut）
- 根据书名或作者获取图书信息不包含该图书的库存信息（BookOut），用户需要找到书的 ISBN 或 bid 再次查询获取库存信息
"""


# 根据主键 bid 获取图书
def get_book_by_bid(inv_repo: IBookInventoryRepository, bid: int, to_dict: bool = True) -> Optional[Dict]:
    books_with_inv = inv_repo.get_inventories_by_bid(book_id = bid)
    if not books_with_inv:
        return None
    # 获取库存表列表中的每个tags对应类别名
    books_with_inv = TagCategory.translate_books(books_with_inv)
    return books_with_inv


# 根据 ISBN 获取图书
def get_book_by_isbn(book_repo: IBookRepository, inv_repo: IBookInventoryRepository, isbn: str, to_dict: bool = True) -> Optional[Dict]:
    books = book_repo.get_book_by_isbn(isbn)
    if not books:
        return None
    books_with_inv = inv_repo.get_inventories_by_bid(book_id = books["bid"]) 
    books_with_inv = TagCategory.translate_books(books_with_inv)
    return books_with_inv

# 根据书名获取图书（可能有多本书同名）
def get_books_by_title(book_repo: IBookRepository, title: str) -> List[Dict]:
    books = book_repo.get_books_by_title(title)
    books = TagCategory.translate_books(books)
    return books


# 根据作者获取图书（可能有多本书同一作者）
def get_books_by_author(book_repo: IBookRepository, author: str) -> List[Dict]:
    books = book_repo.get_books_by_author(author)
    books = TagCategory.translate_books(books)
    return books


# 批量创建图书
def create_batch_books(book_repo: IBookRepository, inv_repo: IBookInventoryRepository,books: List[BookCreate]) -> Dict[str, Any]:
    """
    逐本插入（或增量库存）。每本书按单本逻辑处理：
      - ISBN 已存在 → 在指定 warehouse 上 +1 或新建库存
      - ISBN 不存在 → 先写 books，再写 inventory
    返回: {"success": [BookInventoryOut...], "failed": [{"index": i, "isbn": ..., "error": "..."}]}
    """
    results: Dict[str, Any] = {"success": [], "failed": []}

    for i, book in enumerate(books):
        try:
            # 基本字段健壮性校验（与单本逻辑保持一致）
            if book.tags:
                TagCategory.validate_tag(book.tags)  # 仅校验，不覆盖；如需规范化可用返回值版

            if not book.warehouse_name or not book.warehouse_name.strip():
                raise ValueError("warehouse_name is required for inventory")

            # 直接复用单本逻辑
            inv_out = create_book(book_repo=book_repo, inv_repo=inv_repo, book_data=book)
            # inv_out 期望是 BookInventoryOut 的 dict（含 book: BookOut）
            results["success"].append(inv_out)

        except Exception as e:
            # 保留 index，方便定位本批次中是哪一条失败
            results["failed"].append({
                "index": i,
                "isbn": getattr(book, "isbn", None),
                "warehouse_name": getattr(book, "warehouse_name", None),
                "error": str(e),
            })

    return results


def create_book(book_repo: IBookRepository, inv_repo: IBookInventoryRepository, book_data: BookCreate) -> Dict:  # 返回的是 BookInventoryOut 的 dict
    # 1) 校验 tags
    if book_data.tags:
        TagCategory.validate_tag(book_data.tags)
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
            return updated or inv_repo.get_by_bid_and_warehouse(book_id=book_id, warehouse_name=warehouse_name)
        else:
            # 3.3 无库存 → 新建库存 quantity=1，并返回（含 book 嵌套）
            created = inv_repo.create_inventory(
                BookInventoryCreate(book_id=book_id, warehouse_name=warehouse_name, quantity=1)
            )
            return created
    
    # 4) 不存在图书：先插 books，再插库存，并返回 BookInventoryOut
    payload = book_data.model_dump()
    payload.pop("warehouse_name", None)  # 删掉不属于 Book 的字段
    created_book = book_repo.create_book(BookOnlyCreate(**payload))
    
    book_id = created_book["bid"]
    created_inv = inv_repo.create_inventory(
        BookInventoryCreate(book_id=book_id, warehouse_name=warehouse_name, quantity=1)
    )
    return created_inv









# TODO:以下函数待完善


# 批量查询图书（可分页）
def get_batch_books(repo: IBookRepository, page: int = 0, page_size: int = 10) -> Dict:
    batch_books = repo.get_batch_books(page, page_size)
    # 对返回的每本书，转换tags为类别名称
    for book in batch_books['books']:
        book['tags'] = TagCategory.to_name(book['tags'])
    return batch_books



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
