import pytest
from src.producer_mcp.mcp_server import (
    # Import the LOGIC functions, not the TOOLS
    _list_products_logic,
    _get_product_logic,
    _add_product_logic,
    _get_stats_logic,
    CreateProductRequest,
    Product,
)
from src.data.db import engine, Base, get_db, Product as DBProduct

# --- Fixtures ---


@pytest.fixture(autouse=True)
def reset_db():
    """Setup test database with fresh data for each test."""
    # Drop all tables and recreate
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Add test data
    with get_db() as db:
        db.add(DBProduct(id=1, name="Test Phone", price=100.0, category="Tech", in_stock=True))
        db.add(DBProduct(id=2, name="Test Laptop", price=500.0, category="Tech", in_stock=False))
    
    yield
    
    # Cleanup after test
    Base.metadata.drop_all(bind=engine)


# --- Tests ---


def test_list_products():
    """It should return the current list of products."""
    products = _list_products_logic()  # Call logic directly
    assert len(products) == 2
    assert products[0].name == "Test Phone"


def test_get_product_success():
    """It should return a product if the ID exists."""
    product = _get_product_logic(1)
    assert product.name == "Test Phone"
    assert product.price == 100.0


def test_get_product_not_found():
    """It should raise ValueError if the ID does not exist."""
    with pytest.raises(ValueError, match="not found"):
        _get_product_logic(999)


def test_add_product():
    """It should add a product and generate a new ID."""
    new_request = CreateProductRequest(
        name="New Gadget", price=250.0, category="Home", in_stock=True
    )

    result = _add_product_logic(new_request)

    assert result.id == 3  # Auto-incremented from existing 1, 2
    assert result.name == "New Gadget"
    
    # Verify it's actually in the database
    all_products = _list_products_logic()
    assert len(all_products) == 3


def test_get_stats():
    """It should calculate correct count and average."""
    stats = _get_stats_logic()
    assert stats["total_products"] == 2
    assert stats["average_price"] == 300.0


def test_get_stats_empty():
    """It should handle empty database without crashing."""
    # Clear the database
    with get_db() as db:
        db.query(DBProduct).delete()
    
    stats = _get_stats_logic()
    assert stats["total_products"] == 0
    assert stats["average_price"] == 0.0
    assert stats["average_price"] == 0.0
