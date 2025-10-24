from fastapi import APIRouter, Depends, HTTPException
from app.schemas.book import BookCreate, BookOut, BatchBooksOut, BookUpdate
from app.core.biz_response import BizResponse
from app.service import book_svc
from sqlalchemy.orm import Session
from app.storage.database import get_book_repo
from app.storage.database import get_bookinv_repo
from app.storage.book.book_interface import IBookRepository
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from typing import List
from sqlalchemy.exc import IntegrityError

books_router = APIRouter(prefix="/books", tags=["books"])

@books_router.post("/")  # 不要写 response_model
def create_book(book: BookCreate, book_repo: IBookRepository = Depends(get_book_repo), inv_repo: IBookInventoryRepository = Depends(get_bookinv_repo)):
    try:
        result = book_svc.create_book(book_repo=book_repo, inv_repo=inv_repo, book_data=book)
        return BizResponse(data=result)  # 统一外壳
    except ValueError as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except IntegrityError:
        # 比如并发下 ISBN 唯一约束冲突
        return BizResponse(data=None, msg="Duplicate ISBN", status_code=409)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)
    

# 批量添加图书
@books_router.post("/batch")
def create_batch(payload: List[BookCreate], book_repo: IBookRepository = Depends(get_book_repo), inv_repo: IBookInventoryRepository = Depends(get_bookinv_repo)):
    try:
        result = book_svc.create_batch_books(book_repo, inv_repo, payload)
        # 约定：只要有成功项就 200；全失败可视情况返回 207/207 Multi-Status 或 400
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

@books_router.get("/id/{bid}")
def get_inventories_by_bid(bid: int, inv_repo: IBookInventoryRepository = Depends(get_bookinv_repo)):
    try:
        items = book_svc.get_book_by_bid(inv_repo=inv_repo, bid=bid)  # List[dict]
        if not items:
            return BizResponse(data=[], msg="No books found with this book_id", status_code=404)
        return BizResponse(data=items)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 获取图书信息（根据ISBN查询）
@books_router.get("/isbn/{isbn}")
def get_book_by_isbn(isbn: str, book_repo: IBookRepository = Depends(get_book_repo), inv_repo: IBookInventoryRepository = Depends(get_bookinv_repo)):
    try:
        items = book_svc.get_book_by_isbn(book_repo, inv_repo, isbn)
        if not items:
            return BizResponse(data=[], msg="No books found with this isbn", status_code=404)
        return BizResponse(data=items)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 获取图书信息（根据书名查询）
@books_router.get("/title/{title}")
def get_books_by_title(title: str, book_repo: IBookRepository = Depends(get_book_repo)):
    try:
        books = book_svc.get_books_by_title(book_repo, title)
        if books:
            return BizResponse(data=books)
        else:
            return BizResponse(data=[], msg="No books found with this title", status_code=404)
    except Exception as e:
        return BizResponse(data=[], msg=str(e), status_code=500)

# 获取图书信息（根据作者查询）
@books_router.get("/author/{author}")
def get_books_by_author(author: str, book_repo: IBookRepository = Depends(get_book_repo)):
    try:
        books = book_svc.get_books_by_author(book_repo, author)
        if books:
            return BizResponse(data=books)
        else:
            return BizResponse(data=[], msg="No books found with this author", status_code=404)
    except Exception as e:
        return BizResponse(data=[], msg=str(e), status_code=500)





# TODO: 以下接口功能待完善

# 获取图书信息（批量查询，支持分页）
@books_router.get("/", response_model=BatchBooksOut)
def get_books(page: int = 0, page_size: int = 10, repo: IBookRepository = Depends(get_book_repo)):
    try:
        result = book_svc.get_batch_books(repo, page, page_size)
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)


# 更新图书信息
@books_router.put("/{bid}", response_model=BookOut)
def update_book(bid: int, book_update: BookUpdate, repo: IBookRepository = Depends(get_book_repo)):
    try:
        updated_book = book_svc.update_book(repo, bid, book_update)
        if updated_book:
            return BizResponse(data=updated_book)
        else:
            return BizResponse(data=None, msg=f"Update failed: {bid} not found", status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 删除图书
@books_router.delete("/{bid}", response_model=BookOut)
def delete_book(bid: int, repo: IBookRepository = Depends(get_book_repo)):
    try:
        book_svc.delete_book(repo, bid)
        return BizResponse(data=True)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)
