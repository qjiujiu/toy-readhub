# domain_exceptions.py
from fastapi import HTTPException, status


class LocationNotFound(Exception):
    def __init__(self, isbn: str, warehouse_name: str, candidates: list[str] | None = None):
        super().__init__(f"Location not found for ISBN '{isbn}' with warehouse_name '{warehouse_name}'")
        self.isbn = isbn
        self.warehouse_name = warehouse_name
        self.candidates = candidates or []

class UpdateFailed(Exception):
    def __init__(self, loc_id: int):
        super().__init__(f"Update failed for loc_id={loc_id}")
        self.loc_id = loc_id

class CreateOrderFailed(Exception):
    def __init__(self, user_id: int, book_id: int):
        super().__init__(f"Create order failed for user_id={user_id}, book_id={book_id}")
        self.book_id = book_id
        self.user_id = user_id

class FieldRequiredError(HTTPException):
    def __init__(self, field: str):
        detail = f"The field '{field}' is required and cannot be empty."
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class StudentIDAlreadyExists(HTTPException):
    def __init__(self, student_id: str):
        detail = f"Student ID '{student_id}' already exists"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class StudentNotFound(Exception):
    def __init__(self, entity: str, identifier: str):
        self.status_code = 404
        self.detail = f"StudentNotFound, No {entity} found with identifier: {identifier}"
    def __str__(self):
        return self.detail

class OrderNotFound(HTTPException):
    def __init__(self, entity: str, identifier: str):
        self.status_code = 404
        self.detail = f"OrderNotFound, No {entity} found with identifier: {identifier}"
    def __str__(self):
        return self.detail

class StatusNotFound(Exception):
    def __init__(self, entity: str, identifier: str):
        self.status_code = 404
        self.detail = f"StatusNotFound, No {entity} found with identifier: {identifier}"
    def __str__(self):
        return self.detail

class BookNotFound(Exception):
    def __init__(self, entity: str, identifier: str):
        self.status_code = 404
        self.detail = f"BookNotFound, No {entity} found with identifier: {identifier}"
    def __str__(self):
        return self.detail


class InsufficientStockError(Exception):
    def __init__(self, isbn: str, warehouse_name: str):
        self.isbn = isbn
        self.warehouse_name = warehouse_name
        self.message = f"Book with ISBN {isbn} in warehouse {warehouse_name} is out of stock."
        super().__init__(self.message)

class OrderStatusError(Exception):
    def __init__(self):
        self.message = f"Order has already been returned, cannot update status"
        super().__init__(self.message)

class UserisRestricted(Exception):
    def __init__(self, uid):
        self.message = f"User {uid} has already been restricted, cannot create order"
        self.uid = uid
        super().__init__(self.message)

class InvalidCredentialsError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

