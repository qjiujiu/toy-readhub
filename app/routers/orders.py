from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas, database
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 添加学生借阅信息
@router.post("/", response_model=schemas.BookOrderOut)
def create_book_order(order: schemas.BookOrderCreate, db: Session = Depends(get_db)):
    # 设置还书日期为借书日期后的30天
    if not order.return_date:  # 如果没有提供还书日期，则设置为借书日期后30天
        order.return_date = datetime.now() + timedelta(days=30)
    return crud.create_book_order(db=db, book_order=order)

# 获取所有书本借阅记录
@router.get("/books", response_model=list[schemas.BookOrderOut])
def get_book_orders(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_book_orders(db=db, skip=skip, limit=limit)

# 获取某名学生借阅记录
@router.get("/students/{student_id}", response_model=list[schemas.BookOrderOut])
def get_student_orders(student_id: int, db: Session = Depends(get_db)):
    return crud.get_student_orders(db=db, student_id=student_id)

# 获取某一本书的借阅记录
@router.get("/books/{book_id}", response_model=list[schemas.BookOrderOut])
def get_book_borrow_records(book_id: int, db: Session = Depends(get_db)):
    return crud.get_book_borrow_records(db=db, book_id=book_id)