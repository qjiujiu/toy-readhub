from sqlalchemy import Column, Integer, String
from .database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, DateTime
from datetime import datetime

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(15), nullable=True)
    
    # 关联借书订单
    orders = relationship("BookOrder", back_populates="student")


class BookOrder(Base):
    __tablename__ = "book_orders"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    borrow_date = Column(DateTime, default=datetime.utcnow)
    return_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="borrowed")  # borrowed, returned

    # 关联到学生和书籍
    student = relationship("Student", back_populates="orders")
    book = relationship("Book", back_populates="orders")

Book.orders = relationship("BookOrder", back_populates="book")

