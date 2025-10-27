# app/storage/book_location/book_location_sqlalchemy.py
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_
from app.core.db import transaction
from app.models.book_location import BookLocation  # ORM 模型（类名请确保为 BookLocation）
from app.models.book_inventory import BookInventory 
from app.schemas.book_location import (
    BookLocationCreate,
    BookLocationUpdate,
    BookLocationOut,
    BookDetailOut
)
from app.schemas.book import BookOut
from app.schemas.book_inventory import BookInventoryOut
from app.storage.book_location.book_location_interface import IBookLocationRepository
from app.core.logx import logger

class SQLAlchemyBookLocationRepository(IBookLocationRepository):
    def __init__(self, db: Session):
        self.db = db

    # 按 book_id 获取所有位置
    def get_locations_by_bid(self, book_id: int) -> List[Dict]:
        rows = (
        self.db.query(BookLocation)
        .options(
            selectinload(BookLocation.book),
            selectinload(BookLocation.inventory),  # 预加载一对一库存关系
        )
        .filter(BookLocation.book_id == book_id)
        .order_by(BookLocation.warehouse_name.asc(), BookLocation.loc_id.asc())
        .all()
        )
        result: List[Dict] = []
        for r in rows:
            detail = BookDetailOut(
                book=BookOut.model_validate(r.book),
                quantity=r.inventory.quantity,
                warehouse_name=r.warehouse_name,
                area=r.area,
                floor=r.floor
            )
            result.append(detail.model_dump())

        return result

    # 按 (book_id, warehouse_name) 获取唯一位置（业务定义为“一书一馆一条”）
    def get_by_bid_and_warehouse(self, book_id: int, warehouse_name: str) -> Dict:
        name = (warehouse_name or "").strip()
        row = (
            self.db.query(BookLocation)
            .filter(
                and_(
                    BookLocation.book_id == book_id,
                    BookLocation.warehouse_name == name,
                )
            )
            .one_or_none()
        )
        if not row:
            return None
        return BookLocationOut.model_validate(row).model_dump()

    # 按 loc_id 获取
    def get_by_loc_id(self, loc_id: int) -> Optional[Dict]:
        row = (
            self.db.query(BookLocation)
            .options(selectinload(BookLocation.book))
            .filter(BookLocation.loc_id == loc_id)
            .one_or_none()
        )
        return None if not row else BookLocationOut.model_validate(row).model_dump()

    # 新增位置
    def create_location(self, loc_data: BookLocationCreate) -> Dict:
        name = (loc_data.warehouse_name or "").strip()
        obj = BookLocation(
            book_id=loc_data.book_id,
            warehouse_name=name,
            area=(loc_data.area or None),
            floor=(loc_data.floor or None),
        )
        with transaction(self.db):
            self.db.add(obj)
        self.db.refresh(obj)
        _ = obj.book  # 确保关系已加载
        inv = obj.inventory
        if not inv:
            raise ValueError(
                f"Inventory not found for book_id={loc_data.book_id}, warehouse_name='{name}'. "
                "Please create inventory before creating location."
            )
        result = BookDetailOut(
            book=BookOut.model_validate(obj.book),
            warehouse_name=obj.warehouse_name,
            area=obj.area,
            floor=obj.floor,
            quantity=obj.inventory.quantity,
            )
        return result.model_dump()

    # 更新图书的位置信息（通过loc_id）
    def update_location(self, loc_id: int, loc_data: BookLocationUpdate) -> Optional[Dict]:
        location = self.db.query(BookLocation).filter(BookLocation.loc_id == loc_id).one_or_none()
        if not location:
            return None

        with transaction(self.db):
            for field, value in loc_data.dict(exclude_unset=True).items():
                setattr(location, field, value)
            
        self.db.refresh(location)
        return BookLocationOut.model_validate(location).model_dump()


    # 批量删除：按书ID（返回删除条数）
    def delete_all_by_book_id(self, book_id: int) -> int:
        rows = self.db.query(BookLocation).filter(BookLocation.book_id == book_id).all()
        if not rows:
            return 0
        count = len(rows)
        with transaction(self.db):
            for r in rows:
                self.db.delete(r)
        return count
    


    # # 删除：按主键
    # def delete_by_loc_id(self, loc_id: int) -> None:
    #     row = self.db.query(BookLocation).filter(BookLocation.loc_id == loc_id).one_or_none()
    #     if not row:
    #         raise ValueError(f"Location {loc_id} not found.")
    #     with transaction(self.db):
    #         self.db.delete(row)

    # # 删除：按 (book_id, warehouse_name)
    # def delete_by_bid_and_warehouse(self, book_id: int, warehouse_name: str) -> None:
    #     name = (warehouse_name or "").strip()
    #     rows = (
    #         self.db.query(BookLocation)
    #         .filter(
    #             and_(
    #                 BookLocation.book_id == book_id,
    #                 BookLocation.warehouse_name == name,
    #             )
    #         )
    #         .all()
    #     )
    #     if not rows:
    #         raise ValueError(f"Location for book_id={book_id}, warehouse_name='{name}' not found.")
    #     with transaction(self.db):
    #         for r in rows:
    #             self.db.delete(r)

