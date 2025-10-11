from typing import Protocol, Optional, List, Union, Dict
from app.schemas.user import UserCreate, UserUpdate, UserOut

# 这是一个接口协议(也可以使用Python ABC抽象基类实现, 此处使用Protocol会更简洁)
# 使用 Protocol 定义接口时，不需要像 ABC 一样创建一个类继承树，子类不需要继承协议，而只要实现协议中的方法即可
class IUserRepository(Protocol):
    def get_user_by_uid(self, uid: int) -> Optional[UserOut]:
        ...

    def get_user_by_student_id(self, student_id: str) -> Optional[UserOut]: 
        ...
    
    def get_batch_users(self, page: int, page_size: int) -> List[UserOut]: 
        ...
    
    def create_user(self, user_data: UserCreate) -> UserOut: 
        ...


    def create_batch(self, users: List[UserCreate]) -> List[UserOut]: 
        ...
    
    
    def update_user(self, student_id: str, user_data: UserUpdate) -> Optional[UserOut]: 
        ...
    
    def delete_user(self, student_id: str) -> None: 
        ...