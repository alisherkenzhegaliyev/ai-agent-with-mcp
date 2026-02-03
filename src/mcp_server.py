from fastmcp import FastMCP
import json
from pydantic import BaseModel
from typing import List, Dict

JSON_FILE = "products.json"


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


# --- Server Setup ---
mcp = FastMCP("MCP")
products_data: List[Product] = []

# --- Load Data ---
try:
    with open(JSON_FILE, "r") as file:
        raw = json.load(file)
        products_data = [Product(**item) for item in raw]
except (FileNotFoundError, FileExistsError):
    print("Can't find file, starting with empty database.")
except json.JSONDecodeError:
    print("Can't decode json, starting with empty database.")
except Exception as e:
    print(f"Data validation error: {e}")

# --- Tools ---


@mcp.tool()
def list_products() -> List[Product]:
    """
    List all available products in the database.
    Returns a list of Product objects.
    """
    return products_data


@mcp.tool()
def get_product(product_id: int) -> Product:
    """
    Get a single product by its unique ID.
    Raises ValueError if the product is not found.
    """
    for p in products_data:
        if p.id == product_id:
            return p

    raise ValueError(f"Product with ID {product_id} not found")


@mcp.tool()
def add_product(request: CreateProductRequest) -> Product:
    """
    Add a new product to the database.
    The ID is auto-generated based on the current highest ID.
    """
    new_id = 1
    if products_data:
        new_id = max(p.id for p in products_data) + 1

    product = Product(id=new_id, **request.model_dump())
    products_data.append(product)

    # Save to disk
    with open(JSON_FILE, "w") as f:
        f.write(json.dumps([p.model_dump() for p in products_data], indent=2))

    return product


@mcp.tool()
def get_stats() -> Dict[str, float]:
    """
    Get database statistics including total count and average price.
    Returns a dictionary with 'total_products' and 'average_price'.
    """
    total_count = len(products_data)

    if total_count == 0:
        return {"total_products": 0, "average_price": 0.0}

    total_price = sum(p.price for p in products_data)
    average_price = total_price / total_count

    return {"total_products": total_count, "average_price": round(average_price, 2)}
