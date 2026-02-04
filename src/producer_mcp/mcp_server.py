from fastmcp import FastMCP
import json
import sys
from typing import List, Dict
from src.data.product import Product, CreateProductRequest
import os
from src.config.logging import get_logger
from src.data.db import get_db, Product as DBProduct, Base, engine

logger = get_logger(__name__)

# Initialize database tables
Base.metadata.create_all(bind=engine)


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
except (FileNotFoundError, FileExistsError):
    print("Can't find file, starting with empty database.", file=sys.stderr)
except json.JSONDecodeError:
    print("Can't decode json, starting with empty database.", file=sys.stderr)
except Exception as e:
    print(f"Data validation error: {e}", file=sys.stderr)

# These functions are NOT decorated. They are pure Python --> for testing


def _list_products_logic() -> List[Product]:
    with get_db() as db:
        db_products = db.query(DBProduct).all()
        return [Product(**{k: v for k, v in p.__dict__.items() if not k.startswith('_')}) 
                for p in db_products]


def _get_product_logic(product_id: int) -> Product:
    with get_db() as db:
        db_product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
        if not db_product:
            raise ValueError(f"Product with ID {product_id} not found")
        return Product(**{k: v for k, v in db_product.__dict__.items() if not k.startswith('_')})


def _add_product_logic(request: CreateProductRequest) -> Product:
    with get_db() as db:
        db_product = DBProduct(**request.model_dump())
        db.add(db_product)
        db.flush()  # Get the ID without committing yet
        result = Product(**{k: v for k, v in db_product.__dict__.items() if not k.startswith('_')})
        return result


def _get_stats_logic() -> Dict[str, float]:
    with get_db() as db:
        total_count = db.query(DBProduct).count()
        if total_count == 0:
            return {"total_products": 0, "average_price": 0.0}
        
        total_price = sum(p.price for p in db.query(DBProduct).all())
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
