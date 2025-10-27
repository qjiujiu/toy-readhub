from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.book import BookOut
from app.schemas.book_inventory import BookInventoryOut
class BookLocationCreate(BaseModel):
    book_id: int                                   # 图书ID（必填，外键）
    warehouse_name: str                            # 仓库/馆名（必填）
    area: Optional[str]                            # 所在区域（如 A区、B区）
    floor: Optional[str]                           # 所在楼层（如 1F、2F）

    model_config = ConfigDict(from_attributes=True)


class BookLocationOut(BaseModel):
    loc_id: int                          # 位置记录主键ID
    book_id: int                         # 图书ID（外键）
    warehouse_name: str                  # 仓库/馆名
    area: Optional[str]                  # 所在区域
    floor: Optional[str]                 # 所在楼层
    model_config = ConfigDict(from_attributes=True)


class BookDetailOut(BaseModel):
    book: BookOut                        # 关联的图书信息（嵌套 BookOut）
    warehouse_name: str                  # 仓库/馆名
    area: Optional[str]                  # 所在区域
    floor: Optional[str]                 # 所在楼层
    quantity: int                        # 该书库存量

    model_config = ConfigDict(from_attributes=True)


# 通过bid和warehouse_name 定位图书，更新 area，floor
class BookLocationUpdate(BaseModel):
    # warehouse_name: Optional[str]           # 仓库名称
    # 图书校区和图书库存量绑定，所以不允许更新校区信息
    
    area: Optional[str] = None              # 所在区域 
    floor: Optional[str] = None             # 所在楼层 
    
    model_config = ConfigDict(from_attributes=True)
