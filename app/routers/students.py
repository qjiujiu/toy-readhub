from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas, database

router = APIRouter(
    prefix="/students",
    tags=["students"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 添加学生信息
@router.post("/", response_model=schemas.StudentOut)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    return crud.create_student(db=db, student=student)

# 获取学生信息
@router.get("/", response_model=list[schemas.StudentOut])
def get_students(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_students(db=db, skip=skip, limit=limit)

# 添加学生借阅信息
@router.post("/orders", response_model=schemas.BookOrderOut)
def create_book_order(order: schemas.BookOrderCreate, db: Session = Depends(get_db)):
    return crud.create_book_order(db=db, book_order=order)

# 获取书本借阅记录
@router.get("/orders", response_model=list[schemas.BookOrderOut])
def get_book_orders(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_book_orders(db=db, skip=skip, limit=limit)

# 获取学生借阅记录
@router.get("/{student_id}/orders", response_model=list[schemas.BookOrderOut])
def get_student_orders(student_id: int, db: Session = Depends(get_db)):
    return crud.get_student_orders(db=db, student_id=student_id)