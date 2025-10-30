from typing import List, Dict, Optional, Any
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate, BatchOrdersOut
from app.storage.order.order_interface import IOrderRepository
from app.storage.user.user_interface import IUserRepository
from app.storage.book.book_interface import IBookRepository
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from app.schemas.order import OrderStatus
from app.core.exceptions import OrderNotFound, OrderStatusError, InsufficientStockError, StudentNotFound, BookNotFound  # 假设已定义错误类
from app.core.logx import logger


# 创建借阅订单
def create_order(order_repo: IOrderRepository, inv_repo: IBookInventoryRepository, order_data: OrderCreate) -> Dict:
    # 在此调用数据层方法来创建新借阅订单
    book_inv = inv_repo.get_by_bid_and_warehouse(book_id=order_data.book_id, warehouse_name=order_data.warehouse_name)
    if book_inv["quantity"] == 0:
        raise InsufficientStockError(book_id=order_data.book_id, warehouse_name=order_data.warehouse_name)
    new_order = order_repo.create_order(order_data)
    inv_repo.update_inventory(book_id=order_data.book_id, warehouse_name=order_data.warehouse_name, delta=-1)
    return new_order


# 批量创建借阅订单
def create_batch_orders(order_repo: IOrderRepository, inv_repo: IBookInventoryRepository, orders: List[OrderCreate]) -> Dict[str, Any]:
    """
    批量创建借阅订单，每个订单按单本逻辑处理：
      - 如果库存不足 → 抛出 InsufficientStockError 错误
      - 如果库存足够 → 创建借阅订单并减少库存
    返回：
    {
        "success": [OrderOut...],                 # 成功的借阅订单
        "failed": [{"index": i, "error": "..."}]  # 失败的借阅订单及错误信息
    }
    """
    results: Dict[str, Any] = {"success": [], "failed": []}

    for i, order in enumerate(orders):
        try:
            # 检查库存
            book_inv = inv_repo.get_by_bid_and_warehouse(book_id=order.book_id, warehouse_name=order.warehouse_name)
            if book_inv["quantity"] == 0:
                raise InsufficientStockError(book_id=order.book_id, warehouse_name=order.warehouse_name)

            # 创建借阅订单
            new_order = order_repo.create_order(order_data=order)

            # 更新库存
            inv_repo.update_inventory(book_id=order.book_id, warehouse_name=order.warehouse_name, delta=-1)

            # 成功后将订单添加到成功结果列表
            results["success"].append(new_order)
        except InsufficientStockError as e:
            # 库存不足错误
            results["failed"].append({
                "index": i,
                "error": f"Insufficient stock: {str(e)}"
            })
        except Exception as e:
            # 其他异常处理
            results["failed"].append({
                "index": i,
                "error": str(e)
            })
    return results

# 批量查询借阅订单（可分页）
def get_batch_orders(repo: IOrderRepository, page: int = 0, page_size: int = 10) -> Dict:
    orders = repo.get_batch_orders(page=page, page_size=page_size)
    return orders

# 基于订单号获取借阅订单
def get_order_by_oid(repo: IOrderRepository, order_id: int) -> Optional[Dict]:
    order = repo.get_order_by_oid(order_id)
    if not order:
        raise OrderNotFound(entity="oid", identifier=order_id)
    return order

# 获取特定用户的借阅订单
def get_orders_by_sid(user_repo:IUserRepository, order_repo: IOrderRepository, student_id: str, page: int = 0, page_size: int = 10) -> List[Dict]:
    user_info = user_repo.get_user_by_student_id(student_id=student_id)
    if not user_info:
        raise StudentNotFound(entity="student_id", identifier=student_id)
    orders = order_repo.get_orders_by_uid(user_info.uid, page, page_size)
    if not orders:
        raise OrderNotFound(entity="student_id", identifier=student_id)
    return [order.model_dump() for order in orders]

# 获取特定图书的借阅订单
def get_order_by_isbn(book_repo: IBookRepository, order_repo: IOrderRepository, isbn: str, page: int = 0, page_size: int = 10) -> List[Dict]:
    book_info = book_repo.get_book_by_isbn(isbn=isbn)
    if not book_info:
        raise BookNotFound(isbn)
    orders = order_repo.get_order_by_bid(book_id=book_info["bid"], page=page, page_size=page_size)
    if not orders:
        raise OrderNotFound(entity="isbn", identifier=isbn)
    return [order.model_dump() for order in orders]
    

# 更新订单状态(还书，挂失等)
def update_order_status(order_repo: IOrderRepository, inv_repo: IBookInventoryRepository, order_id: str, status: OrderStatus) -> Optional[Dict]:
    order = order_repo.get_order_by_oid(order_id)
    if not order:
        raise OrderNotFound(entity="order_id", identifier=order_id)

    if order.status == OrderStatus.returned:
        raise OrderStatusError("Order has already been returned, cannot update status.")
    
    # 更新订单状态
    order_data = OrderUpdate(status=status)
    updated_order = order_repo.update_order(order_id, order_data)
    
    # 还书修改库存
    if status == OrderStatus.returned:
        inv_repo.update_inventory(book_id=updated_order["book_id"], warehouse_name=update_order["warehouse_name"], delta=1)

    return updated_order








# TODO 下面功能待完善





# 更新借阅订单
def update_order(repo: IOrderRepository, order_id: str, order_data: OrderUpdate) -> Optional[Dict]:
    updated_order = repo.update_order(order_id, order_data)
    if not updated_order:
        raise OrderNotFound(order_id)
    return updated_order.model_dump()  # 返回更新后的订单数据


# 删除借阅订单
def delete_order(repo: IOrderRepository, order_id: str) -> None:
    order = repo.get_order_by_id(order_id)
    if not order:
        raise OrderNotFound(order_id)
    repo.delete_order(order_id)  # 删除订单

# 批量删除借阅订单
def delete_batch_orders(repo: IOrderRepository, order_ids: List[str]) -> None:
    for order_id in order_ids:
        order = repo.get_order_by_id(order_id)
        if not order:
            raise OrderNotFound(order_id)
        repo.delete_order(order_id)
    return {"status": "success", "message": f"{len(order_ids)} orders deleted successfully."}
