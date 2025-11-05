from typing import Optional, Dict, List, Any
from app.schemas.book import (
    BookCreate,
    BookUpdate,
    BookOnlyCreate,
    BookDetailOut,
    BookDeleteOut
)
from app.storage.book.book_interface import IBookRepository  
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from app.storage.book_location.book_location_interface import IBookLocationRepository
from app.schemas.book_inventory import (
    BookInventoryCreate
)
from app.schemas.book_location import BookLocationCreate, BookLocationUpdate
from app.models.book import TagCategory
from app.core.logx import logger

from app.core.exceptions import BookNotFound, LocationNotFound, UpdateFailed

logger.is_debug(True)


"""
读取图书功能：
- 获取图书详细信息获取图书详细信息（BookDetailOut）包含基本信息，库存信息，存储位置信息
    - 根据图书主键 bid 查找
    - 根据图书 isbn 和 warehouse_name 查找

- 获取获取图书基本信息（BookOut），用户需要找到书的 ISBN 或 bid 再次查询获取详细信息
    - 根据图书 ISBN 查找
    - 根据书名 title 查找
    - 根据作者 author 查找
"""


# 根据主键 bid 获取图书
def get_book_by_bid(loc_repo: IBookLocationRepository, bid: int, to_dict: bool = True) -> Dict:
    books_with_detail = loc_repo.get_detail_location_by_bid(book_id = bid)
    if not books_with_detail:
        return BookNotFound(entity="bid", identifier=bid)
    # 获取库存表列表中的每个tags对应类别名
    books_with_detail = TagCategory.translate_tags(books_with_detail, nested=False)
    return books_with_detail


# 根据 ISBN 获取图书（可能有多本相同的书，返回其中一本图书的基本信息）
def get_book_by_isbn(book_repo: IBookRepository, isbn: str) -> Optional[Dict]:
    books = book_repo.get_book_by_isbn(isbn)
    return books

# 根据 ISBN 和 warehouse_name 获取图书唯一位置
def get_book_by_isbn_wn(book_repo: IBookRepository, loc_repo: IBookLocationRepository, isbn: str, warehouse_name: str) -> Dict:
    book_info = book_repo.get_book_by_isbn(isbn=isbn)
    if not book_info:
        raise BookNotFound(entity="isbn", identifier=isbn)
    book_loc = loc_repo.get_by_bid_and_warehouse(book_id=book_info["bid"], warehouse_name=warehouse_name)
    if not book_loc:
        # 同步给出该书当前所有有效馆名，供接口层直接返回提示
        locs: List[dict] = loc_repo.get_locations_by_isbn(isbn=isbn) or []
        logger.debug(locs)
        candidates = sorted({l.get("warehouse_name") for l in locs if l.get("warehouse_name")})
        raise LocationNotFound(isbn=isbn, warehouse_name=warehouse_name, candidates=candidates) 
    return book_loc

# 根据书名获取图书（可能有多本书同名）
def get_books_by_title(book_repo: IBookRepository, title: str) -> List[Dict]:
    books = book_repo.get_books_by_title(title)
    books = TagCategory.translate_tags(books, nested=False)
    return books


# 根据作者获取图书（可能有多本书同一作者）
def get_books_by_author(book_repo: IBookRepository, author: str) -> List[Dict]:
    books = book_repo.get_books_by_author(author)
    books = TagCategory.translate_tags(books, nested=False)
    return books

# 批量查询图书（可分页）
def get_batch_books(book_repo: IBookRepository, page: int = 0, page_size: int = 10) -> Dict:
    batch_books = book_repo.get_batch_books(page, page_size)
    # 对返回的每本书，转换tags为类别名称
    batch_books = TagCategory.translate_tags(batch_books, nested=True)

    return batch_books


# 批量创建图书
def create_batch_books(book_repo: IBookRepository, inv_repo: IBookInventoryRepository, loc_repo: IBookLocationRepository, books: List[BookCreate]) -> Dict[str, Any]:
    """
    逐本插入（或增量库存）。每本书按单本逻辑处理：
      - ISBN 已存在 → 在指定 warehouse 上 +1 或新建库存和位置
      - ISBN 不存在 → 先写 books，再写 inventory, 最后写 location
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
            loc_out = create_book(book_repo=book_repo, inv_repo=inv_repo, loc_repo=loc_repo, book_data=book)
            # loc_out 期望是 BookLocationOut 的 dict（含 book: BookOut, book_inventory: BookInventoryOut）
            results["success"].append(loc_out)

        except Exception as e:
            # 保留 index，方便定位本批次中是哪一条失败
            results["failed"].append({
                "index": i,
                "isbn": getattr(book, "isbn", None),
                "warehouse_name": getattr(book, "warehouse_name", None),
                "error": str(e),
            })

    return results

# 插入一本图书
def create_book(book_repo: IBookRepository, inv_repo: IBookInventoryRepository, loc_repo: IBookLocationRepository, book_data: BookCreate) -> Dict:  # 返回的是 BookInventoryOut 的 dict
    # 1) 校验 tags
    if book_data.tags:
        TagCategory.validate_tag(book_data.tags)
    # 2) 校验库存必要信息：warehouse_name
    if not book_data.warehouse_name or not book_data.warehouse_name.strip():
        raise ValueError("warehouse_name is required for inventory")
    warehouse_name = book_data.warehouse_name.strip()
    isbn = book_data.isbn
    
    # 3)无论是否存在同 ISBN 的图书都直接插入book 和 book_location(插入book_location 功能在最后面)
    payload = book_data.model_dump()
    payload.pop("warehouse_name", None)  # 删掉不属于 Book 的字段, warehouse_name, area, floor
    payload.pop("area", None)
    payload.pop("floor", None)
    created_book = book_repo.create_book(BookOnlyCreate(**payload))
    # 4) 查该仓库是否已有库存
    inv = inv_repo.get_by_isbn_and_warehouse(isbn=isbn, warehouse_name=warehouse_name)
    if inv:
        # 4.1 已有库存 → 数量 +1
        book_inv = inv_repo.update_inventory(isbn=isbn, warehouse_name=warehouse_name, delta=1)
    else:
        # 3.3 无库存 → 新建库存 quantity=1，新建位置
        inv_repo.create_inventory(BookInventoryCreate(isbn=isbn, warehouse_name=warehouse_name, quantity=1))
            
    created = loc_repo.create_location(
                BookLocationCreate(book_id=created_book.bid, isbn=isbn, warehouse_name=warehouse_name, area=book_data.area, floor=book_data.floor)
            )
    return created



# 更新图书的基本信息（通过 bid）
def update_book_info(book_repo: IBookRepository, bid: int, book_data: BookUpdate) -> Optional[Dict]:
    updated_book = book_repo.update_book_info(bid, book_data)
    if not updated_book:
        return None
    updated_book = TagCategory.translate_tag(updated_book)
    return updated_book


# 更新图书的位置信息（通过 bid）
def update_book_loc(loc_repo: IBookLocationRepository, bid: int, loc_data: BookLocationUpdate) -> Optional[Dict]:
    book_loc = loc_repo.get_location_by_bid(book_id=bid)
    if not book_loc:
        raise BookNotFound("bid", bid)
    
    updated_book_loc = loc_repo.update_location(loc_id=book_loc["loc_id"], loc_data=loc_data)
    
    if not updated_book_loc:
        raise UpdateFailed(loc_id=book_loc["loc_id"])

    updated_book_loc = TagCategory.translate_tag(updated_book_loc)
    return updated_book_loc

# 删除图书（通过 bid）
def delete_book_by_bid(book_repo: IBookRepository, loc_repo: IBookLocationRepository, inv_repo: IBookInventoryRepository, bid: int) -> Optional[Dict]:
    """
    业务层：按 bid 删除一本书基本信息及其关联的“位置”和“库存”。

    删除顺序：
      1) 先删位置 book_locations
      2) 再删库存 book_inventory
      3) 最后删图书 books
    返回：删除摘要 dict；如果书不存在，返回 None
    """
    # 1) 查书
    book = book_repo.get_book_by_bid(bid=bid)
    isbn = book["isbn"]
    book_detail = loc_repo.get_detail_location_by_bid(book_id=bid)
    warehouse_name = book_detail["warehouse_name"]
    if not book:
        return BookNotFound(entity="bid", identifier=bid)

    # 2) 删除位置
    try:
        deleted_locs = loc_repo.delete_by_bid(book_id=bid)  # 返回已删除位置信息 BookLocationOut
    except Exception as e:
        logger.exception("delete_loctaion_by_bid failed: %s", e)
        raise

    # 3) 删除库存
    try:
        book_inv = inv_repo.get_by_isbn_and_warehouse(isbn=isbn, warehouse_name=warehouse_name)
        if book_inv["quantity"] > 1:
            updated_invs = inv_repo.update_inventory(isbn=isbn, warehouse_name=warehouse_name,delta=-1)
        else:
            updated_invs = inv_repo.delete_inventory(isbn)  # 返回删除更新前的库存信息BookInventoryOut
    except Exception as e:
        logger.exception("delete_inventory_by_ISBN failed: %s", e)
        raise 
    # 4) 删除图书
    deleted_book_snapshot = book_repo.delete_book_by_bid(bid=bid)  # 返回图书基本信息 BookOut
    return BookDeleteOut(book=deleted_book_snapshot, deleted_locations=deleted_locs, updated_inventory=updated_invs).model_dump()