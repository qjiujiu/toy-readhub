from typing import Protocol, Optional, List
from app.schemas.order import OrderStatus, OrderStatus, OrderOut, OrderUpdate,BatchOrdersOut

class IOrderRepository(Protocol):
    pass