# domain_exceptions.py
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
