from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas, database

router = APIRouter(
    prefix="/books",
    tags=["books"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 查询所有图书, skip 跳过多少条, limit 表示返回多少条，分页用
@router.get("/", response_model=list[schemas.BookOut])
def read_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_books(db, skip=skip, limit=limit)

# 通过id查询单本图书
@router.get("/{book_id}", response_model=schemas.BookOut)
def read_book(book_id: int, db: Session = Depends(get_db)):
    db_book = crud.get_book(db, book_id=book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return db_book

# 添加图书
@router.post("/", response_model=schemas.BookOut)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    return crud.create_book(db=db, book=book)

# 更新图书
@router.put("/{book_id}", response_model=schemas.BookOut)
def update_book(book_id: int, book: schemas.BookUpdate, db: Session = Depends(get_db)):
    db_book = crud.update_book(db=db, book_id=book_id, book=book)
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return db_book

# 通过id删除图书
@router.delete("/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = crud.delete_book(db=db, book_id=book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}

# 批量插入书
@router.post("/batch", response_model=list[schemas.BookOut])
def create_books(books: list[schemas.BookCreate], db: Session = Depends(get_db)):
    db_books = []
    for book in books:
        db_book = crud.create_book(db=db, book=book)
        db_books.append(db_book)
    return db_books