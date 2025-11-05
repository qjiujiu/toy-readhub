from pydantic import BaseModel, conint, Field, ConfigDict
from typing import Optional

class BookInventoryCreate(BaseModel):
    isbn: str                         # 图书 ISBN（必填）
    warehouse_name: Optional[str]     # 仓库名称
    quantity: int = Field(..., ge=0)  # 库存数量（必填，必须是非负整数）
                                      # Field 用于为 Pydantic 模型字段添加更多的验证规则。ge=0 表示字段值必须大于或等于 0。
                                      # ...：表示该字段是必填项

    model_config = ConfigDict(from_attributes=True)

class BookInventoryOut(BaseModel):
    inv_id: int                       # 库存 ID
    isbn: str                         # 图书 ISBN
    warehouse_name: Optional[str]     # 仓库名称
    quantity: int                     # 当前库存数量

    model_config = ConfigDict(from_attributes=True)


class BookInventoryUpdate(BaseModel):
    quantity: int = Field(..., ge=0)  # 库存数量（可以更新）

    model_config = ConfigDict(from_attributes=True)