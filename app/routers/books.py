from fastapi import APIRouter, Depends, HTTPException
from app.schemas.book import BookCreate, BookOut, BatchBooksOut, BookUpdate
from app.core.biz_response import BizResponse
from app.service import book_svc
from sqlalchemy.orm import Session
from app.storage.database import get_book_repo
from app.storage.book.book_interface import IBookRepository
from typing import List

router = APIRouter()

# 创建单本图书
@router.post("/", response_model=BookOut)
def create_book(book: BookCreate, repo: IBookRepository = Depends(get_book_repo)):
    try:
        new_book = book_svc.create_book(repo, book)
        return BizResponse(data=new_book)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 批量添加图书
@router.post("/batch", response_model=BatchBooksOut)
def create_batch_books(books: List[BookCreate], repo: IBookRepository = Depends(get_book_repo)):
    try:
        new_books = book_svc.create_batch_books(repo, books)
        return BizResponse(data=new_books)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 获取图书信息（批量查询，支持分页）
@router.get("/", response_model=BatchBooksOut)
def get_books(page: int = 0, page_size: int = 10, repo: IBookRepository = Depends(get_book_repo)):
    try:
        result = book_svc.get_batch_books(repo, page, page_size)
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)

# 获取图书信息（根据图书ID查询）
@router.get("/{bid}", response_model=BookOut)
def get_book_by_bid(bid: int, repo: IBookRepository = Depends(get_book_repo)):
    try:
        book = book_svc.get_book_by_bid(repo, bid)
        if book:
            return BizResponse(data=book)
        else:
            return BizResponse(data=None, msg="Book not found", status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 获取图书信息（根据ISBN查询）
@router.get("/isbn/{isbn}", response_model=BookOut)
def get_book_by_isbn(isbn: str, repo: IBookRepository = Depends(get_book_repo)):
    try:
        book = book_svc.get_book_by_isbn(repo, isbn)
        if book:
            return BizResponse(data=book)
        else:
            return BizResponse(data=None, msg="Book not found", status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 获取图书信息（根据书名查询）
@router.get("/title/{title}", response_model=List[BookOut])
def get_books_by_title(title: str, repo: IBookRepository = Depends(get_book_repo)):
    try:
        books = book_svc.get_books_by_title(repo, title)
        if books:
            return BizResponse(data=books)
        else:
            return BizResponse(data=[], msg="No books found with this title", status_code=404)
    except Exception as e:
        return BizResponse(data=[], msg=str(e), status_code=500)

# 获取图书信息（根据作者查询）
@router.get("/author/{author}", response_model=List[BookOut])
def get_books_by_author(author: str, repo: IBookRepository = Depends(get_book_repo)):
    try:
        books = book_svc.get_books_by_author(repo, author)
        if books:
            return BizResponse(data=books)
        else:
            return BizResponse(data=[], msg="No books found with this author", status_code=404)
    except Exception as e:
        return BizResponse(data=[], msg=str(e), status_code=500)

# 更新图书信息
@router.put("/{bid}", response_model=BookOut)
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
@router.delete("/{bid}", response_model=BookOut)
def delete_book(bid: int, repo: IBookRepository = Depends(get_book_repo)):
    try:
        book_svc.delete_book(repo, bid)
        return BizResponse(data=True)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)
