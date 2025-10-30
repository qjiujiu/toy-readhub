from typing import Protocol, Optional, List, Union, Dict
from app.schemas.user_restrictions import UserRestrictionCreate, UserRestrictionUpdate
from datetime import datetime

# 这是一个接口协议(也可以使用Python ABC抽象基类实现, 此处使用Protocol会更简洁)
# 使用 Protocol 定义接口时，不需要像 ABC 一样创建一个类继承树，子类不需要继承协议，而只要实现协议中的方法即可
class IUserRestrictionsRepository(Protocol):
    """用户借阅限制表的数据层接口协议（Protocol）"""

    # 读取：按 user_id 获取当前限制记录
    def get_by_user_id(self, user_id: int) -> Optional[Dict]:
        ...

    # 判断：用户当前是否受限（可结合惰性解禁）
    def is_restricted(self, user_id: int, auto_clear_expired: bool = True) -> bool:
        ...

    # 创建：新增限制记录（一个用户仅一条，若已存在可抛错或改用 upsert）
    def create(self, data: UserRestrictionCreate) -> Dict:
        ...

    def create_batch_for_user_ids(self, user_ids: list[int]) -> dict:
        ...

    # 更新：按 user_id 部分更新（解除/延长/修改原因）
    def update(self, user_id: int, data: UserRestrictionUpdate) -> Optional[Dict]:
        ...

    # 删除：按 user_id 删除限制记录
    def delete_by_user_id(self, user_id: int) -> bool:
        ...

    # 惰性解禁：若限制已过期则自动解除并返回最新记录
    def auto_clear_if_expired(self, user_id: int) -> Optional[Dict]:
        ...

    # 批量解禁：清除所有已过期限制；返回受影响条数
    def bulk_auto_clear_expired(self, now: Optional[datetime] = None) -> int:
        ...