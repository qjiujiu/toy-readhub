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
            # 预加载 book 与 inventory，避免后续再次触发 SQL
            .options(
                selectinload(BookLocation.book),
                selectinload(BookLocation.inventory),
            )
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
        detail = BookDetailOut(
            book=BookOut.model_validate(row.book),
            warehouse_name=row.warehouse_name,
            area=row.area,
            floor=row.floor,
            quantity=row.inventory.quantity
        )
        return detail.model_dump()

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

    # 部分字段更新（仅更新传入且非 None 的字段；字段名需与列一致）
    def patch_location(self, loc_id: int, **fields) -> Optional[Dict]:
        row = self.db.query(BookLocation).filter(BookLocation.loc_id == loc_id).one_or_none()
        if not row:
            return None

        # 仅对存在的列且值非 None 的项进行更新
        updatable = {"warehouse_name", "area", "floor"}
        changed = False
        for k, v in fields.items():
            if k in updatable and v is not None:
                val = v.strip() if isinstance(v, str) else v
                setattr(row, k, val)
                changed = True

        if changed:
            with transaction(self.db):
                self.db.add(row)
            self.db.refresh(row)

        return BookLocationOut.model_validate(row).model_dump()

    # 整体更新（按请求体）
    def update_location(self, loc_id: int, loc_data: BookLocationUpdate) -> Optional[Dict]:
        row = self.db.query(BookLocation).filter(BookLocation.loc_id == loc_id).one_or_none()
        if not row:
            return None

        # 仅当传入值不为 None 时更新（避免覆盖为 None）
        if loc_data.warehouse_name is not None:
            row.warehouse_name = loc_data.warehouse_name.strip()
        if loc_data.area is not None:
            row.area = loc_data.area.strip() if loc_data.area else None
        if loc_data.floor is not None:
            row.floor = loc_data.floor.strip() if loc_data.floor else None

        with transaction(self.db):
            self.db.add(row)
        self.db.refresh(row)
        _ = row.book
        return BookLocationOut.model_validate(row).model_dump()

    # 删除：按主键
    def delete_by_loc_id(self, loc_id: int) -> None:
        row = self.db.query(BookLocation).filter(BookLocation.loc_id == loc_id).one_or_none()
        if not row:
            raise ValueError(f"Location {loc_id} not found.")
        with transaction(self.db):
            self.db.delete(row)

    # 删除：按 (book_id, warehouse_name)
    def delete_by_bid_and_warehouse(self, book_id: int, warehouse_name: str) -> None:
        name = (warehouse_name or "").strip()
        rows = (
            self.db.query(BookLocation)
            .filter(
                and_(
                    BookLocation.book_id == book_id,
                    BookLocation.warehouse_name == name,
                )
            )
            .all()
        )
        if not rows:
            raise ValueError(f"Location for book_id={book_id}, warehouse_name='{name}' not found.")
        with transaction(self.db):
            for r in rows:
                self.db.delete(r)

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

