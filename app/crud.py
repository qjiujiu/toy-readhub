from sqlalchemy.orm import Session
from app import models, schemas

def get_books(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Book).offset(skip).limit(limit).all()

def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id == book_id).first()

def create_book(db: Session, book: schemas.BookCreate):
    db_book = models.Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def update_book(db: Session, book_id: int, book: schemas.BookUpdate):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        for key, value in book.dict().items():
            setattr(db_book, key, value)
        db.commit()
        db.refresh(db_book)
    return db_book

def delete_book(db: Session, book_id: int):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        db.delete(db_book)
        db.commit()
    return db_book

def create_student(db: Session, student: schemas.StudentCreate):
    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# 学生相关操作
def get_students(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Student).offset(skip).limit(limit).all()

def create_book_order(db: Session, book_order: schemas.BookOrderCreate):
    db_order = models.BookOrder(**book_order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

# 借书订单
def get_book_orders(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.BookOrder).offset(skip).limit(limit).all()

def get_student_orders(db: Session, student_id: int):
    return db.query(models.BookOrder).filter(models.BookOrder.student_id == student_id).all()


def student_exists(db: Session, student_id: int) -> bool:
    return db.query(models.Student.id).filter(models.Student.id == student_id).first() is not None

def book_exists(db: Session, book_id: int) -> bool:
    return db.query(models.Book.id).filter(models.Book.id == book_id).first() is not None

def get_order(db: Session, order_id: int):
    return db.query(models.BookOrder).filter(models.BookOrder.id == order_id).first()

def mark_order_returned(db: Session, order_id: int, return_date):
    order = get_order(db, order_id)
    if not order:
        return None
    order.status = "returned"
    order.return_date = return_date
    db.commit()
    db.refresh(order)
    return order