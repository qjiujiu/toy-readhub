from pydantic import BaseModel, ConfigDict
from typing import Optional, List

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
    area: Optional[str] = None
    floor: Optional[str] = None
    tags: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# 返回的图书信息
class BookOut(BaseModel):
    bid: int                        # 图书 ID
    title: str                      # 书名
    author: str                     # 作者
    isbn: str                       # 国际标准书号
    abstract: Optional[str]         # 图书简介
    area: Optional[str]             # 所在区域
    floor: Optional[str]            # 所在楼层
    tags: Optional[str]             # 图书标签

    model_config = ConfigDict(from_attributes=True)

# 更新图书的请求体
class BookUpdate(BaseModel):
    title: Optional[str]            # 书名（可更新）
    author: Optional[str]           # 作者（可更新）
    isbn: Optional[str]             # 国际标准书号（可更新）
    abstract: Optional[str]         # 图书简介（可更新）
    area: Optional[str]             # 所在区域（可更新）
    floor: Optional[str]            # 所在楼层（可更新）
    tags: Optional[str]             # 图书标签（可更新）

    warehouse_name: Optional[str]   # 仓库名称(图书存放的校区)

    model_config = ConfigDict(from_attributes=True)

# 返回批量图书信息的响应体
class BatchBooksOut(BaseModel):
    total: int                # 总记录数
    count: int                # 当前返回的记录数
    books: List[BookOut]      # 图书列表

    model_config = ConfigDict(from_attributes=True)