from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas, database
from datetime import datetime, timedelta
from app.routers.auth import get_current_student
from pydantic import BaseModel

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

# 添加学生借阅信息（管理员/馆员使用：显式传 student_id）
@router.post("/", response_model=schemas.BookOrderOut)
def create_book_order(order: schemas.BookOrderCreate, db: Session = Depends(get_db)):
    # 1) 学生是否存在（已注册）
    if not crud.student_exists(db, order.student_id):
        raise HTTPException(status_code=400, detail="Student not registered in the system")

    # 2) 书是否存在
    if not crud.book_exists(db, order.book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    # 3) 还书日期：默认=借书日期+30天（如果未提供）
    if not order.return_date:
        # 若你的 BookOrderCreate 要求 borrow_date 必传，这里可直接用它
        base_date = order.borrow_date or datetime.utcnow()
        order.return_date = base_date + timedelta(days=30)

    return crud.create_book_order(db=db, book_order=order)

# —— 登录态借书（学生本人下单）——
class BorrowMePayload(BaseModel):
    book_id: int
    borrow_date: datetime

@router.post("/me", response_model=schemas.BookOrderOut)
def create_book_order_for_me(payload: BorrowMePayload,
                             db: Session = Depends(get_db),
                             me=Depends(get_current_student)):
    # 书是否存在
    if not crud.book_exists(db, payload.book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    order = schemas.BookOrderCreate(
        book_id=payload.book_id,
        student_id=me.id,  # 绑定当前登录学生
        borrow_date=payload.borrow_date,
        return_date=payload.borrow_date + timedelta(days=30),
        status="borrowed",
    )
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

# —— 还书（管理员/馆员操作）——
@router.put("/{order_id}/return", response_model=schemas.BookOrderOut)
def return_book(order_id: int,
                return_date: datetime | None = None,
                db: Session = Depends(get_db)):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 如果学生记录被删除，则视为非注册，不允许还书（你也可以选择允许并仅修改订单状态）
    if not crud.student_exists(db, order.student_id):
        raise HTTPException(status_code=400, detail="Student not registered in the system")

    rd = return_date or datetime.utcnow()
    updated = crud.mark_order_returned(db, order_id, rd)
    return updated

# —— 登录态还书（学生本人操作，且必须是自己的订单）——
@router.put("/me/{order_id}/return", response_model=schemas.BookOrderOut)
def return_my_book(order_id: int,
                   return_date: datetime | None = None,
                   db: Session = Depends(get_db),
                   me=Depends(get_current_student)):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 只能归还“自己的借阅单”
    if order.student_id != me.id:
        raise HTTPException(status_code=403, detail="You can only return your own orders")

    rd = return_date or datetime.utcnow()
    updated = crud.mark_order_returned(db, order_id, rd)
    return updated
