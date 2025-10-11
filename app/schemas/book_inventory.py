from pydantic import BaseModel, conint, Field
from typing import Optional
from app.schemas.book import BookOut  # 假设你已经定义了 BookOut 用于输出图书信息

class BookInventoryCreate(BaseModel):
    book_id: int                      # 图书 ID（必填）
    warehouse_name: Optional[str]     # 仓库名称
    quantity: int = Field(..., ge=0)  # 库存数量（必填，必须是非负整数）
                                      # Field 用于为 Pydantic 模型字段添加更多的验证规则。ge=0 表示字段值必须大于或等于 0。
                                      # ...：表示该字段是必填项
    class Config:
        orm_mode = True  # 支持从 ORM 模型转换为 Pydantic 模型


class BookInventoryOut(BaseModel):
    inv_id: int                       # 库存 ID
    book_id: int                      # 图书 ID
    warehouse_name: Optional[str]     # 仓库名称
    quantity: int                     # 当前库存数量
    book: BookOut                     # 关联的图书信息（嵌套 BookOut）

    class Config:
        orm_mode = True  # 支持从 ORM 模型转换为 Pydantic 模型


class BookInventoryUpdate(BaseModel):
    quantity: int = Field(..., ge=0)  # 库存数量（可以更新）

    class Config:
        orm_mode = True  # 支持从 ORM 模型转换为 Pydantic 模型
