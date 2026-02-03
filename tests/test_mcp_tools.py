import pytest
from unittest.mock import patch, mock_open
from src.mcp.mcp_server import (
    # Import the LOGIC functions, not the TOOLS
    _list_products_logic,
    _get_product_logic,
    _add_product_logic,
    _get_stats_logic,
    CreateProductRequest,
    Product,
)
import src.mcp.mcp_server as server_module

# --- Fixtures ---


@pytest.fixture(autouse=True)
def reset_db():
    server_module.products_data = [
        Product(id=1, name="Test Phone", price=100.0, category="Tech", in_stock=True),
        Product(id=2, name="Test Laptop", price=500.0, category="Tech", in_stock=False),
    ]


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
    with patch("builtins.open", mock_open()):
        new_request = CreateProductRequest(
            name="New Gadget", price=250.0, category="Home", in_stock=True
        )

        result = _add_product_logic(new_request)

        assert result.id == 3
        assert result.name == "New Gadget"
        assert len(server_module.products_data) == 3


def test_get_stats():
    """It should calculate correct count and average."""
    stats = _get_stats_logic()
    assert stats["total_products"] == 2
    assert stats["average_price"] == 300.0


def test_get_stats_empty():
    """It should handle empty database without crashing."""
    server_module.products_data = []
    stats = _get_stats_logic()
    assert stats["total_products"] == 0
    assert stats["average_price"] == 0.0
