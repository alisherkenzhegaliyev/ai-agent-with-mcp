from fastmcp import FastMCP
import json
import sys
from typing import List, Dict
from src.data.product import Product, CreateProductRequest
import os
from src.config.logging import get_logger

logger = get_logger(__name__)


# Get the path relative to this file's location
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(CURRENT_DIR, "..", "data", "products.json")

# --- Server Setup ---
mcp = FastMCP("MCP")
products_data: List[Product] = []

# --- Load Data ---
try:
    with open(JSON_FILE, "r") as file:
        raw = json.load(file)
        products_data = [Product(**item) for item in raw]
    logger.info(f"Loaded {len(products_data)} products from {JSON_FILE}")
except (FileNotFoundError, FileExistsError):
    logger.warning("Can't find file, starting with empty database.")
    print("Can't find file, starting with empty database.", file=sys.stderr)
except json.JSONDecodeError:
    logger.error("Can't decode json, starting with empty database.")
    print("Can't decode json, starting with empty database.", file=sys.stderr)
except Exception as e:
    logger.error(f"Data validation error: {e}")
    print(f"Data validation error: {e}", file=sys.stderr)

# These functions are NOT decorated. They are pure Python --> for testing


def _list_products_logic() -> List[Product]:
    return products_data


def _get_product_logic(product_id: int) -> Product:
    for p in products_data:
        if p.id == product_id:
            return p
    raise ValueError(f"Product with ID {product_id} not found")


def _add_product_logic(request: CreateProductRequest) -> Product:
    new_id = 1
    if products_data:
        new_id = max(p.id for p in products_data) + 1

    product = Product(id=new_id, **request.model_dump())
    products_data.append(product)

    # Save to disk
    with open(JSON_FILE, "w") as f:
        f.write(json.dumps([p.model_dump() for p in products_data], indent=2))

    return product


def _get_stats_logic() -> Dict[str, float]:
    total_count = len(products_data)
    if total_count == 0:
        return {"total_products": 0, "average_price": 0.0}

    total_price = sum(p.price for p in products_data)
    average_price = total_price / total_count

    return {"total_products": total_count, "average_price": round(average_price, 2)}


# --- MCP TOOLS ---
# These just wrap the logic for the AI.


@mcp.tool()
def list_products() -> List[Product]:
    """List all available products in the database."""
    logger.info("Tool invoked: list_products")
    return _list_products_logic()


@mcp.tool()
def get_product(product_id: int) -> Product:
    """Get a single product by its unique ID."""
    logger.info(f"Tool invoked: get_product(product_id={product_id})")
    return _get_product_logic(product_id)


@mcp.tool()
def add_product(
    name: str, price: float, category: str, in_stock: bool = True
) -> Product:
    """Add a new product. ID is auto-generated."""
    logger.info(f"Tool invoked: add_product(name={name}, price={price}, category={category})")
    request = CreateProductRequest(
        name=name, price=price, category=category, in_stock=in_stock
    )
    return _add_product_logic(request)


@mcp.tool()
def get_stats() -> Dict[str, float]:
    """Get database statistics."""
    logger.info("Tool invoked: get_stats")
    return _get_stats_logic()


if __name__ == "__main__":
    mcp.run()
