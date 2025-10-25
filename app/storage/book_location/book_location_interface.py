# app/storage/book_location/book_location_interface.py
from typing import Optional, Protocol, List, Dict
from app.schemas.book_location import (
    BookLocationCreate,
    BookLocationUpdate,
    BookLocationOut,
)

class IBookLocationRepository(Protocol):
    """图书存储位置表（book_locations）数据访问接口协议"""

    # 按图书ID获取该书的所有位置记录（可按仓库名排序）
    def get_locations_by_bid(self, book_id: int) -> List[Dict]:
        ...

    # 按 (book_id, warehouse_name) 获取唯一位置记录
    def get_by_bid_and_warehouse(self, book_id: int, warehouse_name: str) -> Optional[Dict]:
        ...

    # 按 loc_id 获取单条位置记录
    def get_by_loc_id(self, loc_id: int) -> Optional[Dict]:
        ...

    # 新增位置记录
    def create_location(self, loc_data: BookLocationCreate) -> Dict:
        ...

    # 部分字段更新（仅更新非 None 字段）
    def patch_location(self, loc_id: int, **fields) -> Optional[Dict]:
        ...

    # 通过 loc_id 按请求体整体更新（常用：area/floor/warehouse_name）
    def update_location(self, loc_id: int, loc_data: BookLocationUpdate) -> Optional[Dict]:
        ...

    # 删除：按主键
    def delete_by_loc_id(self, loc_id: int) -> None:
        ...

    # 删除：按 (book_id, warehouse_name)
    def delete_by_bid_and_warehouse(self, book_id: int, warehouse_name: str) -> None:
        ...

    # 批量删除：按 book_id
    def delete_all_by_book_id(self, book_id: int) -> int:
        ...
