from pydantic import BaseModel


# --- Data Schemas ---
class Product(BaseModel):
    id: int
    name: str
    price: float
    category: str
    in_stock: bool


class CreateProductRequest(BaseModel):
    name: str
    price: float
    category: str
    in_stock: bool
