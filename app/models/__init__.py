# app/models/__init__.py
from app.models.user import User
from app.models.order import Order
from app.models.book import Book  
from app.models.user_restrictions import UserRestriction
__all__ = ["User", "Order", "Book"]
