from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate, BatchOrdersOut
from app.storage.order.order_interface import IOrderRepository
from typing import Optional, List
from app.core.db import transaction
from datetime import datetime, timezone, timedelta
from app.schemas.order import OrderStatus
from app.core.logx import logger
from sqlalchemy.orm import joinedload

class SQLAlchemyOrderRepository(IOrderRepository):
    def __init__(self, db: Session):
        self.db = db

    # 创建借阅订单
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
        return_time = new_order.calculate_return_time(borrow_time)  # 30秒默认时长
        new_order.return_time = return_time  # 设置计算得到的还书时间

        # 提交事务（如果创建时有修改 return_time）
        with transaction(self.db):
            self.db.commit()
        return OrderOut.model_validate(new_order).model_dump() 
    
    # 获取所有订单
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
    
    # 根据订单ID oid 获取借阅订单
    def get_order_by_oid(self, order_id: int) -> Optional[OrderOut]:
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        return OrderOut.model_validate(order) if order else None

    
    # 根据用户ID uid 获取借阅订单
    def get_orders_by_uid(self, user_id: int) -> List[OrderOut]:
        # 获取特定用户的借阅记录
        orders = (
            self.db.query(Order)
            .filter(Order.user_id == user_id)
            .all()
        )
        return [OrderOut.model_validate(order) for order in orders]
    
    # 根据图书ID bid 获取借阅订单
    def get_order_by_bid(self, book_id: int)-> OrderOut:
        order = self.db.query(Order).filter(Order.book_id == book_id).first()
        if not order:
            return None
        return OrderOut.model_validate(order)

    # 根据图书状态 status 获取借阅订单
    def get_orders_by_status(self, status: OrderStatus, page: int = 0, page_size: int = 10) -> BatchOrdersOut:
        # 查询符合状态的订单
        total = self.db.query(Order).filter(Order.status == status).count()
        orders = (
            self.db.query(Order)
            .filter(Order.status == status)
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )
        return BatchOrdersOut(total=total, count=len(orders), orders=[OrderOut.model_validate(order) for order in orders])

    def update_order(self, order_id: str, order_data: OrderUpdate) -> Optional[OrderOut]:
        # 更新借阅订单状态或归还时间
        order = self.db.query(Order).filter(Order.order_id == order_id).first()

        if order:
            # 更新订单状态
            if order_data.status:
                order.status = order_data.status

            # 根据状态处理归还时间
            if order_data.status == OrderStatus.returned:
                order.actual_return_time = datetime.now(timezone(timedelta(hours=8)))             # 如果状态是归还，设置归还时间为当前时间

            with transaction(self.db):
                self.db.commit()  # 提交更改

            return OrderOut.model_validate(order)

        return None
    

    # 删除借阅订单
    def delete_order(self, order_id: int) -> OrderOut:
        order = self.db.query(Order).options(joinedload(Order.book), joinedload(Order.user)).filter(Order.order_id == order_id).first()
        # 使用 joinedload 来确保 book 和 user 在删除之前就被加载
        # 否者，删除order之后就无法加载关联的book和user，响应体OrderOut处会报错
        if order:
            # 使用事务管理器删除订单
            with transaction(self.db):
                self.db.delete(order)  # 从会话中删除订单
                self.db.commit()  # 提交更改
            return OrderOut.model_validate(order).model_dump() # 返回已删除订单的详细信息
        return None
    
    def delete_orders_by_status(self, status: OrderStatus) -> BatchOrdersOut:
        # 查询所有符合指定状态的订单，并加载关联的 book 和 user
        orders = self.db.query(Order).options(joinedload(Order.book), joinedload(Order.user)).filter(Order.status == status).all()
        total = len(orders)  # 获取符合条件的订单总数
        if not orders:
            return None  # 如果没有符合条件的订单，返回空列表
        
        deleted_orders = []
        
        # 使用事务管理器删除订单
        with transaction(self.db):
            for order in orders:
                self.db.delete(order)  # 从会话中删除订单
                deleted_orders.append(OrderOut.model_validate(order).model_dump())  # 将已删除的订单添加到删除结果中
            self.db.commit()  # 提交更改
        
        return BatchOrdersOut(total=total, count=len(deleted_orders), orders=deleted_orders)
    