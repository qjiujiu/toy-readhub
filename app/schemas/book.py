from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from app.schemas.book_inventory import BookInventoryOut
from app.schemas.book_location import BookLocationOut

# 创建图书的请求体
class BookCreate(BaseModel):
    title: str                      # 书名（必填）
    author: str                     # 作者（必填）
    isbn: str                       # 国际标准书号，唯一（必填）
    abstract: Optional[str]         # 图书简介（可为空）
    area: Optional[str]             # 所在区域（如 A-Z 区）
    floor: Optional[str]            # 所在楼层（如 1F, 2F）
    tags: Optional[str]             # 图书标签（多个标签用逗号分隔）

    warehouse_name: Optional[str]   # 仓库名称(图书存放的校区)

    # Pydantic 将自动将对象实例转换为字典并进行验证
    model_config = ConfigDict(from_attributes=True)

class BookOnlyCreate(BaseModel):
    title: str
    author: str
    isbn: str
    abstract: Optional[str] = None
    tags: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# 返回的图书信息
class BookOut(BaseModel):
    bid: int                        # 图书 ID
    title: str                      # 书名
    author: str                     # 作者
    isbn: str                       # 国际标准书号
    abstract: Optional[str]         # 图书简介
    tags: Optional[str]             # 图书标签

    model_config = ConfigDict(from_attributes=True)


class BookDetailOut(BaseModel):
    book: BookOut                        # 关联的图书信息（嵌套 BookOut）
    warehouse_name: str                  # 仓库/馆名
    area: Optional[str]                  # 所在区域
    floor: Optional[str]                 # 所在楼层
    quantity: int                        # 该书库存量

    model_config = ConfigDict(from_attributes=True)

# 更新图书的请求体
class BookUpdate(BaseModel):
    title: Optional[str] = None            # 书名（可更新）
    author: Optional[str] = None          # 作者（可更新）
    isbn: Optional[str] = None             # 国际标准书号（可更新）
    abstract: Optional[str] = None         # 图书简介（可更新）
    tags: Optional[str] = None             # 图书标签（可更新）

    model_config = ConfigDict(from_attributes=True, extra="forbid")
    # extra="forbid" 禁止传入额外字段

# 返回批量图书信息的响应体
class BatchBooksOut(BaseModel):
    total: int                # 总记录数
    count: int                # 当前返回的记录数
    book: List[BookOut]      # 图书列表
    # 这里本应取名books，但是为了适配工具TagCategory.translate_tags工具，改为book

    model_config = ConfigDict(from_attributes=True)

class BookDeleteOut(BaseModel):
    book: BookOut
    deleted_locations: BookLocationOut
    updated_inventory: BookInventoryOut

    model_config = ConfigDict(from_attributes=True)