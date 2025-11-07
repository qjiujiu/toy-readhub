from typing import List, Dict, Optional, Any
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate, BatchOrdersOut
from app.schemas.user_credit import UserCreditUpdate
from app.storage.order.order_interface import IOrderRepository
from app.storage.user.user_interface import IUserRepository
from app.storage.book.book_interface import IBookRepository
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from app.storage.user_credit.user_credit_interface import IUserCreditRepository
from app.schemas.order import OrderStatus
from app.core.exceptions import (
    OrderNotFound, 
    OrderStatusError, 
    InsufficientStockError, 
    StudentNotFound, 
    BookNotFound, 
    LocationNotFound,
    CreateOrderFailed,
    UserisRestricted
)
from app.core.logx import logger
from datetime import datetime, timezone, timedelta

TZ8 = timezone(timedelta(hours=8))
def _ensure_aware_local(dt: datetime, tz=TZ8) -> datetime:
    """
    若 dt 为 naive，则按本地时区tz解释（不是转换！是指定）。
    若 dt 为 aware，则转到 tz。
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)



# TODO 返回用户被限制的原因



# 创建借阅订单
def create_order(user_repo: IUserRepository, credit_repo: IUserCreditRepository, order_repo: IOrderRepository, inv_repo: IBookInventoryRepository, book_repo: IBookRepository, order_data: OrderCreate) -> Dict:
    user_info = user_repo.get_user_by_uid(uid=order_data.user_id)
    if not user_info:
        raise StudentNotFound(entity="uid", identifier=order_data.user_id)
    student_id = user_info.student_id

    # 更新用户借阅权限（主要查看是否有图书逾期未还）
    over_due = get_overdue_by_sid(user_repo=user_repo, order_repo=order_repo, credit_repo=credit_repo, student_id=student_id)
    if over_due:
        raise UserisRestricted(uid=order_data.user_id)
    
    # 检查用户借阅权限
    if credit_repo.is_restricted(user_id=order_data.user_id):
        raise UserisRestricted(uid=order_data.user_id)
    
    # 允许借书 
    book_info = book_repo.get_book_by_bid(bid=order_data.book_id)
    if not book_info:
        raise BookNotFound(entity="book_id", identifier=order_data.book_id)
    isbn = book_info["isbn"]
    
    # 检查图书库存
    book_inv = inv_repo.get_by_isbn_and_warehouse(isbn=isbn, warehouse_name=order_data.warehouse_name)
    if not book_inv:
        raise LocationNotFound(isbn=isbn, warehouse_name=order_data.warehouse_name)
    if book_inv["quantity"] == 0:
        raise InsufficientStockError(isbn=isbn, warehouse_name=order_data.warehouse_name)
    
    # 创建 order 订单
    new_order = order_repo.create_order(order_data)
    if new_order:
        inv_repo.update_inventory(isbn=isbn, warehouse_name=order_data.warehouse_name, delta=-1)
    else: 
        raise CreateOrderFailed(book_id=order_data.book_id, user_id=order_data.user_id)
    return new_order


# 批量创建借阅订单
def create_batch_orders(user_repo: IUserRepository, credit_repo: IUserCreditRepository, order_repo: IOrderRepository, inv_repo: IBookInventoryRepository, book_repo: IBookRepository, orders: List[OrderCreate]) -> Dict[str, Any]:
    """
    批量创建借阅订单，每个订单按单本逻辑处理：
    返回：
    {
        "success": [OrderOut...],                 # 成功的借阅订单
        "failed": [{"index": i, "error": "..."}]  # 失败的借阅订单及错误信息
    }
    """
    results: Dict[str, Any] = {"success": [], "failed": []}

    for i, order_data in enumerate(orders):
        try:
            # 调用创建单个借阅订单的业务层函数
            new_order = create_order(user_repo=user_repo, credit_repo=credit_repo, order_repo=order_repo, inv_repo=inv_repo, book_repo=book_repo, order_data=order_data)
            # 如果成功，则将成功的订单记录到结果中
            results["success"].append(new_order)
        except Exception as e:
            # 如果出错，则将失败的信息记录到结果中
            results["failed"].append({"index": i, "error": str(e)})

    return results

# 批量查询借阅订单（可分页）
def get_batch_orders(repo: IOrderRepository, page: int = 0, page_size: int = 10) -> Dict:
    orders = repo.get_batch_orders(page=page, page_size=page_size)
    return orders

# 基于订单号 oid 获取借阅订单
def get_order_by_oid(repo: IOrderRepository, order_id: int) -> Optional[Dict]:
    order = repo.get_order_by_oid(order_id)
    if not order:
        raise OrderNotFound(entity="oid", identifier=order_id)
    return order.model_dump()

# 根据学号 sid 获取特定用户的借阅订单
def get_orders_by_sid(user_repo:IUserRepository, order_repo: IOrderRepository, student_id: str) -> List[Dict]:
    user_info = user_repo.get_user_by_student_id(student_id=student_id)
    if not user_info:
        raise StudentNotFound(entity="student_id", identifier=student_id)
    orders = order_repo.get_orders_by_uid(user_info.uid)
    if not orders:
        raise OrderNotFound(entity="student_id", identifier=student_id)
    return [order.model_dump() for order in orders]


# 返回用户 sid 所有逾期未还的图书订单
def get_overdue_by_sid(user_repo:IUserRepository, order_repo: IOrderRepository, credit_repo: IUserCreditRepository, student_id: str)->List[Dict]:
    user_info = user_repo.get_user_by_student_id(student_id=student_id)
    logger.debug(user_info)
    if not user_info:
        raise StudentNotFound(entity="student_id", identifier=student_id)
    orders = order_repo.get_orders_by_uid(user_info.uid)
    if not orders:
        return []
    now = datetime.now(timezone(timedelta(hours=8)))
    overdue_orders = []
    # 遍历订单，判断是否逾期
    for order in orders:
        # 图书已归还，跳过
        if order.status == "returned":
            continue
        return_time = order.return_time
        if not return_time:
            continue
        # 统一为 aware 再比较
        try:
            rt_aware = _ensure_aware_local(return_time, TZ8)
        except Exception as e:
            logger.exception("normalize return_time failed: %s", e)
            continue

        # 如果已到期
        if rt_aware <= now:
            overdue_orders.append(order.model_dump())

            # 更新用户信用状态（标记为逾期）
            credit_repo.update(
                user_id=order.user_id,
                data=UserCreditUpdate(is_overdue=True)
            )

    return overdue_orders


# 根据图书ID book_id 获取借阅订单 (已归还的记录无法查阅到)
def get_order_by_bid(order_repo: IOrderRepository, book_id: int)-> Dict:
    order = order_repo.get_order_by_bid(book_id=book_id)
    if not order:
        raise OrderNotFound(entity="bid", identifier=book_id)
    return order.model_dump()

# 根据 ISBN 获取特定图书的借阅订单
def get_order_by_isbn(book_repo: IBookRepository, order_repo: IOrderRepository, isbn: str) -> List[Dict]:
    # 获取所有的图书记录，可能返回多个
    book_info = book_repo.get_book_by_isbn(isbn=isbn)
    if not book_info or not book_info.book:  # 如果没有图书记录或书籍列表为空
        raise BookNotFound(entity="isbn", identifier=isbn)
    # 提取所有的 book_id (bid)
    book_ids = [book.bid for book in book_info.book]  # 遍历 book 列表，获取每本书的 bid
    logger.debug(book_ids)
    # 初始化一个空列表用于存储所有借阅订单
    all_orders = []
    # 对于每个 book_id，调用 get_order_by_bid 来查询该图书的借阅订单
    for book_id in book_ids:
        orders = order_repo.get_order_by_bid(book_id=book_id)
        if orders:
            all_orders.extend(orders)  # 合并查询结果

    if not all_orders:
        raise OrderNotFound(entity="isbn", identifier=isbn)
    
    # 构造返回的 BatchOrdersOut 对象
    return BatchOrdersOut(
        total=len(all_orders),                     # 总记录数
        count=len(all_orders),                      # 当前返回的记录数
        orders=[order.model_dump() for order in all_orders]  # 转换每个订单为字典
    )

# 根据借阅状态 status 获取图书借阅订单 
def get_orders_by_status(order_repo: IOrderRepository, status: OrderStatus, page: int = 0, page_size: int = 10)-> List[Dict]:
    result = order_repo.get_orders_by_status(status=status, page=page, page_size=page_size)
    return result

# 更新订单状态(还书，挂失等)
def update_order_status(credit_repo: IUserCreditRepository, order_repo: IOrderRepository, inv_repo: IBookInventoryRepository, book_repo: IBookRepository, order_id: str, status: OrderStatus) -> Optional[Dict]:
    order = order_repo.get_order_by_oid(order_id)
    if not order:
        raise OrderNotFound(entity="order_id", identifier=order_id)

    if order.status == OrderStatus.returned:
        raise OrderStatusError()
    
    book_info = book_repo.get_book_by_bid(order.book_id)
    if not book_info:
        raise BookNotFound(entity="bid", identifier=order.book_id)
    isbn = book_info["isbn"]
    order_data = OrderUpdate(status=status)
    # 更新订单状态
    updated_order = order_repo.update_order(order_id, order_data)
    if updated_order.return_time and updated_order.actual_return_time and updated_order.return_time < updated_order.actual_return_time: # 逾期
        overdue_days = (updated_order.actual_return_time - updated_order.return_time).days
        # 至少逾期1天，否则不会进入该条件
        penalty_days = overdue_days * 2
        penalty_until = updated_order.actual_return_time + timedelta(days=penalty_days)

        logger.debug(f"用户 {order.user_id} 逾期 {overdue_days} 天，惩罚 {penalty_days} 天，截止 {penalty_until}")

        # 更新用户信用状态
        credit_repo.update(
            user_id=order.user_id,
            data=UserCreditUpdate(
                is_overdue=True,
                penalty_until=penalty_until
            )
        )
    if updated_order.status == OrderStatus.lost:
        credit_repo.update(user_id=order.user_id, data=UserCreditUpdate(is_lost=True))
    
    if updated_order.status == OrderStatus.returned:
        credit_repo.update(user_id=order.user_id, data=UserCreditUpdate(is_lost=False))

    # 还书修改库存
    if status == OrderStatus.returned:
        inv_repo.update_inventory(isbn=isbn, warehouse_name=updated_order.warehouse_name, delta=1)

    return updated_order

# 删除借阅订单（根据订单号oid）
def delete_order(repo: IOrderRepository, order_id: int) -> Optional[Dict]:
    order = repo.get_order_by_oid(order_id)
    if not order:
        raise OrderNotFound(entity="order_id", identifier=order_id)
    deleted_order = repo.delete_order(order_id=order_id)  # 删除订单
    return deleted_order


# 批量删除借阅订单(删除已归还图书的订单记录)
def delete_batch_orders(repo: IOrderRepository) -> List[Dict]:
    order = repo.get_orders_by_status(status="returned")
    if not order:
        return None
    
    delete_order = repo.delete_orders_by_status(status="returned")
    return delete_order
