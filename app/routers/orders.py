from fastapi import APIRouter, Depends
from app.schemas.order import OrderCreate, OrderOut, BatchOrdersOut, OrderStatus
from app.core.biz_response import BizResponse
from app.service import order_svc
from app.storage.database import get_order_repo, get_bookinv_repo, get_user_repo, get_book_repo, get_usercre_repo
from typing import List
from app.storage.order.order_interface import IOrderRepository
from app.storage.user.user_interface import IUserRepository
from app.storage.book.book_interface import IBookRepository
from app.storage.user_credit.user_credit_interface import IUserCreditRepository
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from app.core.exceptions import (
    OrderNotFound, 
    OrderStatusError, 
    InsufficientStockError, 
    StudentNotFound, 
    BookNotFound, 
    LocationNotFound,
    CreateOrderFailed
)
from app.core.logx import logger
from fastapi.encoders import jsonable_encoder

orders_router = APIRouter(prefix="/orders", tags=["orders"])
# 创建借阅订单
@orders_router.post("/", response_model=OrderOut)
def create_order(order: OrderCreate, user_repo: IUserRepository = Depends(get_user_repo), credit_repo: IUserCreditRepository = Depends(get_usercre_repo), order_repo: IOrderRepository = Depends(get_order_repo), inv_repo: IBookInventoryRepository = Depends(get_bookinv_repo), book_repo: IBookRepository = Depends(get_book_repo)):
    try:
        new_order = order_svc.create_order(user_repo=user_repo, credit_repo=credit_repo, order_repo=order_repo, inv_repo=inv_repo, book_repo=book_repo, order_data=order)
        return BizResponse(data=jsonable_encoder(new_order))
    except BookNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except LocationNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except InsufficientStockError as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except CreateOrderFailed as e:
        return BizResponse(data=None, msg=str(e), status_code=500)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 批量创建借阅订单
@orders_router.post("/batch", response_model=BatchOrdersOut)
def create_batch_orders(orders: List[OrderCreate], user_repo: IUserRepository = Depends(get_user_repo), credit_repo: IUserCreditRepository = Depends(get_usercre_repo), order_repo: IOrderRepository = Depends(get_order_repo), inv_repo: IBookInventoryRepository = Depends(get_bookinv_repo), book_repo: IBookRepository = Depends(get_book_repo)):
    try:
        new_orders = order_svc.create_batch_orders(user_repo=user_repo, credit_repo=credit_repo, order_repo=order_repo, inv_repo=inv_repo, book_repo=book_repo, orders=orders)
        return BizResponse(data=jsonable_encoder(new_orders))
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


# 获取借阅订单（批量查询，支持分页）
@orders_router.get("/", response_model=BatchOrdersOut)
def query_batch_orders(page: int = 0, page_size: int = 10, repo: IOrderRepository = Depends(get_order_repo)):
    try:
        result = order_svc.get_batch_orders(repo=repo, page=page, page_size=page_size)
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)

# 获取借阅订单（根据订单号查询）
@orders_router.get("/oid/{order_id}", response_model=OrderOut)
def query_order(order_id: int, repo: IOrderRepository = Depends(get_order_repo)):
    try:
        order = order_svc.get_order_by_oid(repo=repo, order_id=order_id)
        return BizResponse(data=jsonable_encoder(order))
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 获取借阅订单（根据用户学号student_id查询）
@orders_router.get("/user/{student_id}", response_model=BatchOrdersOut)
def get_orders_by_user_id(student_id: str, oredr_repo: IOrderRepository = Depends(get_order_repo), user_repo: IUserRepository = Depends(get_user_repo)):
    try:
        orders = order_svc.get_orders_by_sid(user_repo=user_repo, order_repo=oredr_repo, student_id=student_id)
        return BizResponse(data=jsonable_encoder(orders))
    except StudentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=[], msg=str(e), status_code=500)

@orders_router.get("/overdue/user/{student_id}")
def get_overdue_by_sid(student_id: str, user_repo:IUserRepository = Depends(get_user_repo), order_repo: IOrderRepository = Depends(get_order_repo), credit_repo: IUserCreditRepository = Depends(get_usercre_repo)):
    try:
        orders = order_svc.get_overdue_by_sid(user_repo=user_repo, order_repo=order_repo, credit_repo=credit_repo, student_id=student_id)
        return BizResponse(data=jsonable_encoder(orders))
    except StudentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=[], msg=str(e), status_code=500)


# 获取借阅订单（根据图书ID bid 查询）已归还的记录无法查到
@orders_router.get("/bid/{book_id}", response_model=BatchOrdersOut)
def get_order_by_bid(book_id: int, order_repo: IOrderRepository = Depends(get_order_repo)):
    try:
        order = order_svc.get_order_by_bid(book_id=book_id, order_repo=order_repo)
        return BizResponse(data=jsonable_encoder(order))
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=[], msg=str(e), status_code=500)

# 获取借阅订单（根据图书isbn查询）
@orders_router.get("/isbn/{isbn}", response_model=BatchOrdersOut)
def get_order_by_isbn(isbn: str, page: int = 0, page_size: int = 10, oredr_repo: IOrderRepository = Depends(get_order_repo), book_repo: IBookRepository = Depends(get_book_repo)):
    try:
        orders = order_svc.get_order_by_isbn(book_repo=book_repo, order_repo=oredr_repo, isbn=isbn, page=page, page_size=page_size)
        return BizResponse(data=jsonable_encoder(orders))
    except BookNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 获取借阅订单（根据图书状态status查询）
@orders_router.get("/status/{status}", response_model=BatchOrdersOut)
def get_orders_by_status(status: OrderStatus, order_repo: IOrderRepository = Depends(get_order_repo), page: int = 0, page_size: int = 10):
    try:
        orders = order_svc.get_orders_by_status(order_repo=order_repo, status=status,page=page, page_size=page_size)
        return BizResponse(data=jsonable_encoder(orders))
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 更新借阅订单状态
@orders_router.put("/{order_id}/{status}", response_model=OrderOut)
def update_order_status(order_id: str, status: str, credit_repo: IUserCreditRepository = Depends(get_usercre_repo), order_repo: IOrderRepository = Depends(get_order_repo), inv_repo: IBookInventoryRepository = Depends(get_bookinv_repo), book_repo: IBookRepository = Depends(get_book_repo)):
    try:
        updated_order = order_svc.update_order_status(credit_repo=credit_repo, order_repo=order_repo, inv_repo=inv_repo, book_repo=book_repo, order_id=order_id, status=status)
        return BizResponse(data=jsonable_encoder(updated_order))
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except OrderStatusError as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 删除借阅订单(根据 oid 删除)
@orders_router.delete("/oid/{order_id}", response_model=OrderOut)
def delete_order(order_id: str, repo: IOrderRepository = Depends(get_order_repo)):
    try:
        order = order_svc.delete_order(repo=repo, order_id=order_id)
        return BizResponse(data=jsonable_encoder(order), msg="Order deleted successfully")
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 批量删除借阅订单（根据订单状态删除，删除所有returned状态的借阅记录）
@orders_router.delete("/batch", response_model=BatchOrdersOut)
def delete_batch_orders(repo: IOrderRepository = Depends(get_order_repo)):
    try:
        result = order_svc.delete_batch_orders(repo=repo)
        return BizResponse(data=jsonable_encoder(result))
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)