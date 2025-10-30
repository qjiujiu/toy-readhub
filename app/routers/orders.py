from fastapi import APIRouter, Depends, HTTPException
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate, BatchOrdersOut
from app.core.biz_response import BizResponse
from app.service import order_svc
from app.storage.database import get_order_repo, get_bookinv_repo, get_user_repo, get_book_repo
from typing import List
from app.storage.order.order_interface import IOrderRepository
from app.storage.user.user_interface import IUserRepository
from app.storage.book.book_interface import IBookRepository
from app.storage.book_inventory.book_inventory_interface import IBookInventoryRepository
from app.core.exceptions import OrderNotFound, OrderStatusError, BookNotFound, StudentNotFound
from app.core.logx import logger
from fastapi.encoders import jsonable_encoder

orders_router = APIRouter(prefix="/orders", tags=["orders"])
# 创建借阅订单
@orders_router.post("/", response_model=OrderOut)
def create_order(order: OrderCreate, order_repo: IOrderRepository = Depends(get_order_repo), inv_repo: IBookInventoryRepository = Depends(get_bookinv_repo)):
    try:
        new_order = order_svc.create_order(order_repo=order_repo, inv_repo=inv_repo, order_data=order)
        return BizResponse(data=jsonable_encoder(new_order))
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 批量创建借阅订单
@orders_router.post("/batch", response_model=BatchOrdersOut)
def create_batch_orders(orders: List[OrderCreate], order_repo: IOrderRepository = Depends(get_order_repo), inv_repo: IBookInventoryRepository = Depends(get_bookinv_repo)):
    try:
        new_orders = order_svc.create_batch_orders(order_repo=order_repo, inv_repo=inv_repo, orders=orders)
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
def get_orders_by_user_id(student_id: str, page: int = 0, page_size: int = 10, oredr_repo: IOrderRepository = Depends(get_order_repo), user_repo: IUserRepository = Depends(get_user_repo)):
    try:
        orders = order_svc.get_orders_by_sid(user_repo=user_repo, order_repo=oredr_repo, student_id=student_id, page=page, page_size=page_size)
        return BizResponse(data=jsonable_encoder(orders))
    except StudentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=[], msg=str(e), status_code=500)

# 获取借阅订单（根据图书isbn查询）
@orders_router.get("/book/{isbn}", response_model=BatchOrdersOut)
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

# 更新借阅订单信息(还书，挂失)
@orders_router.put("/", response_model=OrderOut)
def update_order(order_id: str, order_update: OrderUpdate, repo: IOrderRepository = Depends(get_order_repo)):
    try:
        updated_order = order_svc.update_order(repo=repo, order_id=order_id, order_data=order_update)
        return BizResponse(data=updated_order)
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


# 更新借阅订单状态
@orders_router.put("/{order_id}/status", response_model=OrderOut)
def update_order_status(order_id: str, status: str, repo: IOrderRepository = Depends(get_order_repo)):
    try:
        updated_order = order_svc.update_order_status(repo=repo, order_id=order_id, status=status)
        return BizResponse(data=updated_order)
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except OrderStatusError as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)






# TODO 下面功能待完善


# 删除借阅订单
@orders_router.delete("/{order_id}", response_model=OrderOut)
def delete_order(order_id: str, repo: IOrderRepository = Depends(get_order_repo)):
    try:
        order = order_svc.delete_order(repo=repo, order_id=order_id)
        return BizResponse(data=order, msg="Order deleted successfully")
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# 批量删除借阅订单
@orders_router.delete("/batch", response_model=BatchOrdersOut)
def delete_batch_orders(order_ids: List[str], repo: IOrderRepository = Depends(get_order_repo)):
    try:
        result = order_svc.delete_batch_orders(repo=repo, order_ids=order_ids)
        return BizResponse(data=result)
    except OrderNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)
