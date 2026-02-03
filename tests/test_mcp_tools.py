import pytest
from unittest.mock import patch, mock_open
from src.mcp_server import (
    list_products,
    get_product,
    add_product,
    get_stats,
    CreateProductRequest,
    Product,
)

# import the module itself to reset the global variable
import src.mcp_server as server_module

# --- Fixtures ---> ensures that the state is reset before running each test


@pytest.fixture(autouse=True)
def reset_db():
    """
    Reset the global products_data list before every test.
    This ensures tests are isolated and don't affect each other.
    """
    server_module.products_data = [
        Product(id=1, name="Test Phone", price=100.0, category="Tech", in_stock=True),
        Product(id=2, name="Test Laptop", price=500.0, category="Tech", in_stock=False),
    ]


# --- Tests ---


def test_list_products():
    """It should return the current list of products."""
    products = list_products()
    assert len(products) == 2
    assert products[0].name == "Test Phone"


def test_get_product_success():
    """It should return a product if the ID exists."""
    product = get_product(1)
    assert product.name == "Test Phone"
    assert product.price == 100.0


def test_get_product_not_found():
    """It should raise ValueError if the ID does not exist."""
    with pytest.raises(ValueError, match="not found"):
        get_product(999)


def test_add_product():
    """It should add a product and generate a new ID."""
    # We mock 'open' so we don't actually write to the products.json file
    with patch("builtins.open", mock_open()):
        new_request = CreateProductRequest(
            name="New Gadget", price=250.0, category="Home", in_stock=True
        )

        result = add_product(new_request)

        # Check the return value
        assert result.id == 3  # Should auto-increment from 2
        assert result.name == "New Gadget"

        # Check the actual database state
        assert len(server_module.products_data) == 3


def test_get_stats():
    """It should calculate correct count and average."""
    stats = get_stats()

    # Total: 2 products
    assert stats["total_products"] == 2

    # Average: (100 + 500) / 2 = 300
    assert stats["average_price"] == 300.0


def test_get_stats_empty():
    """It should handle empty database without crashing (division by zero)."""
    server_module.products_data = []  # Manually clear data for this test

    stats = get_stats()
    assert stats["total_products"] == 0
    assert stats["average_price"] == 0.0
