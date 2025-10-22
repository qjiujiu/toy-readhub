from sqlalchemy.orm import Session
from app.models.book import Book
from app.schemas.order import OrderStatus, OrderStatus, OrderOut, OrderUpdate,BatchOrdersOut
from app.storage.order.order_interface import IOrderRepository
from typing import Optional, List, Dict, Union
from app.core.db import transaction


class SQLAlchemyBookRepository(IOrderRepository):
    def __init__(self, db: Session):
        self.db = db