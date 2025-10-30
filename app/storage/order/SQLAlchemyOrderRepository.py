from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate, BatchOrdersOut
from app.storage.order.order_interface import IOrderRepository
from typing import Optional, List
from app.core.db import transaction
from datetime import datetime
from app.schemas.order import OrderStatus
from app.core.logx import logger

class SQLAlchemyOrderRepository(IOrderRepository):
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, order_data: OrderCreate) -> OrderOut:
        """创建新的借阅订单"""
        new_order = Order(
            user_id=order_data.user_id,
            book_id=order_data.book_id,
            warehouse_name=order_data.warehouse_name,
            status=order_data.status
        )

        # 使用事务管理器来将添加新订单到数据库
        with transaction(self.db):  # 确保事务范围
            self.db.add(new_order)  # 将新订单对象添加到会话

        # 通过 `refresh` 获取数据库最新的数据，确保对象内容是最新的
        self.db.refresh(new_order)

        # 调用 calculate_return_time 计算还书时间
        borrow_time = new_order.borrow_time or datetime.utcnow()
        return_time = new_order.calculate_return_time(borrow_time, borrow_duration_seconds=30)  # 30秒默认时长
        new_order.return_time = return_time  # 设置计算得到的还书时间

        # 提交事务（如果创建时有修改 return_time）
        with transaction(self.db):
            self.db.commit()
        return OrderOut.model_validate(new_order).model_dump() 
    
    def get_batch_orders(self, page: int, page_size: int) -> BatchOrdersOut:
        # 获取借阅订单列表并分页
        orders = (
            self.db.query(Order)
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )
        total = self.db.query(Order).count()
        
        return BatchOrdersOut(total=total, count=len(orders), orders=[OrderOut.model_validate(order) for order in orders])
    
    def get_order_by_oid(self, order_id: int) -> Optional[OrderOut]:
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        return OrderOut.model_validate(order).model_dump() if order else None

    def get_orders_by_uid(self, user_id: int, page: int, page_size: int) -> List[OrderOut]:
        # 获取特定用户的借阅记录
        orders = (
            self.db.query(Order)
            .filter(Order.user_id == user_id)
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )
        return [OrderOut.model_validate(order) for order in orders]
    
    def get_order_by_bid(self, book_id: int, page: int, page_size: int)->List[OrderOut]:
        orders = (
            self.db.query(Order)
            .filter(Order.book_id == book_id)
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )
        return [OrderOut.model_validate(order) for order in orders]

    def update_order(self, order_id: str, order_data: OrderUpdate) -> Optional[OrderOut]:
        # 更新借阅订单状态或归还时间
        order = self.db.query(Order).filter(Order.order_id == order_id).first()

        if order:
            # 更新订单状态
            if order_data.status:
                order.status = order_data.status

            # 根据状态处理归还时间
            if order_data.status == OrderStatus.returned:
                order.return_time = datetime.utcnow()             # 如果状态是归还，设置归还时间为当前时间
            elif order_data.status == OrderStatus.lost_and_returned:
                order.return_time = datetime.utcnow()             # 如果是丢失后归还，也设置归还时间为当前时间
                                                                  # 如果是丢失(lost)状态，则不更新归还时间
            with transaction(self.db):
                self.db.commit()  # 提交更改

            return OrderOut.model_validate(order).model_dump()

        return None

    







    # TODO 下面功能待完善
    

    


    def delete_order(self, order_id: str) -> None:
        # 删除借阅订单
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            # 使用事务管理器删除订单
            with transaction(self.db):
                self.db.delete(order)  # 从会话中删除订单
                self.db.commit()  # 提交更改

    