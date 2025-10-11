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

# 批量查询图书（可分页）
def get_batch_books(repo: IBookRepository, page: int = 0, page_size: int = 10) -> Dict:
    batch_books = repo.get_batch_books(page, page_size)
    return batch_books


# 根据主键 bid 获取图书
def get_book_by_bid(repo: IBookRepository, bid: int, to_dict: bool = True) -> Optional[Dict]:
    book = repo.get_book_by_bid(bid)
    if not book:
        return None
    return book


# 根据 ISBN 获取图书
def get_book_by_isbn(repo: IBookRepository, isbn: str, to_dict: bool = True) -> Optional[Dict]:
    book = repo.get_book_by_isbn(isbn)
    if not book:
        return None
    return book


# 根据书名获取图书（可能有多本书同名）
def get_books_by_title(repo: IBookRepository, title: str) -> List[Dict]:
    books = repo.get_books_by_title(title)
    return books


# 根据作者获取图书（可能有多本书同一作者）
def get_books_by_author(repo: IBookRepository, author: str) -> List[Dict]:
    books = repo.get_books_by_author(author)
    return books


# 批量创建图书
def create_batch_books(repo: IBookRepository, books: List[BookCreate]) -> Dict:
    batch_books = repo.create_batch_books(books)
    return batch_books


# # 创建单本图书
# def create_book(repo: IBookRepository, book_data: BookCreate) -> Dict:
#     new_book = repo.create_book(book_data)
#     return new_book


# 创建单本图书
def create_book(repo: IBookRepository, inventory_repo: IBookInventoryRepository, book_data: BookCreate) -> Dict:
    # 1. 检查图书是否已存在
    existing_book = repo.get_book_by_isbn(book_data.isbn)
    
    if not existing_book:
        # 2. 如果图书不存在，创建新图书
        new_book = repo.create_book(book_data)

        # 3. 创建库存信息，并将初始库存为 1
        inventory_data = BookInventoryCreate(
            book_id=new_book["bid"],  # 获取新创建的图书ID
            warehouse_name=book_data.warehouse_name
        )
        new_inventory = inventory_repo.create_inventory(inventory_data)
        
        return {"book": new_book, "inventory": new_inventory}  # 返回新创建的图书和库存信息

    else:
        # 4. 如果图书已存在，检查该图书在指定仓库的库存
        book_id = existing_book["bid"]  # 获取现有图书的ID

        # 5. 查找该图书在对应仓库的库存记录
        existing_inventory = inventory_repo.get_inventory_by_book_id(book_id)
        
        if existing_inventory:
            # 6. 如果库存记录已存在，且仓库名称相同，更新库存数量
            
            # TODO 这里的库存量没有更新 

            if existing_inventory["warehouse_name"] == book_data.warehouse_name:
                inventory_data = BookInventoryCreate(
                    book_id=book_id,
                    warehouse_name=book_data.warehouse_name
                )
                # 更新库存
                updated_inventory = inventory_repo.update_inventory(book_id, inventory_data)
                return {"book": existing_book, "inventory": updated_inventory}
            else:
                # 7. 如果仓库名称不同，则在 `book_inventory` 表中创建新的库存记录
                inventory_data = BookInventoryCreate(
                    book_id=book_id,
                    warehouse_name=book_data.warehouse_name
                )
                new_inventory = inventory_repo.create_inventory(inventory_data)
                return {"book": existing_book, "inventory": new_inventory}
        else:
            # 8. 如果该图书没有库存记录，新增库存记录
            inventory_data = BookInventoryCreate(
                book_id=book_id,
                warehouse_name=book_data.warehouse_name
            )
            new_inventory = inventory_repo.create_inventory(inventory_data)
            return {"book": existing_book, "inventory": new_inventory}


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
