# domain_exceptions.py
from fastapi import HTTPException, status
class BookNotFound(Exception):
    def __init__(self, isbn: str):
        super().__init__(f"ISBN '{isbn}' not found")
        self.isbn = isbn

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
        self.detail = f"No {entity} found with identifier: {identifier}"

class OrderNotFound(HTTPException):
    def __init__(self, entity: str, identifier: str):
        self.status_code = 404
        self.detail = f"No {entity} found with identifier: {identifier}"


class InsufficientStockError(Exception):
    def __init__(self, book_id: int, warehouse_name: str):
        self.book_id = book_id
        self.warehouse_name = warehouse_name
        self.message = f"Book with ID {book_id} in warehouse {warehouse_name} is out of stock."
        super().__init__(self.message)

class OrderStatusError():
    ...

