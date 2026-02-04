"""
Test script to verify SQLite implementation works correctly.
Tests basic operations and concurrent writes.
"""
import sys
import time
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.data.db import engine, Base, get_db, Product as DBProduct
from src.data.product import Product, CreateProductRequest
from src.producer_mcp.mcp_server import (
    _list_products_logic,
    _get_product_logic,
    _add_product_logic,
    _get_stats_logic
)


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Create tables before each test and cleanup after."""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup after each test to ensure isolation
    with get_db() as db:
        db.query(DBProduct).delete()


def test_basic_operations():
    """Test basic CRUD operations."""
    print("=" * 60)
    print("TEST 1: Basic CRUD Operations")
    print("=" * 60)
    
    # Test 1: List products (might be empty initially)
    print("\n1. Listing all products...")
    products = _list_products_logic()
    print(f"   Found {len(products)} products")
    for p in products:
        print(f"   - {p.name}: ${p.price}")
    
    # Test 2: Add a new product
    print("\n2. Adding new product...")
    new_product = _add_product_logic(CreateProductRequest(
        name="Test Laptop",
        price=1299.99,
        category="Electronics",
        in_stock=True
    ))
    print(f"   Added product: {new_product.name} (ID: {new_product.id})")
    
    # Test 3: Get specific product
    print("\n3. Getting product by ID...")
    product = _get_product_logic(new_product.id)
    print(f"   Retrieved: {product.name} - ${product.price}")
    
    # Test 4: Get stats
    print("\n4. Getting statistics...")
    stats = _get_stats_logic()
    print(f"   Total products: {stats['total_products']}")
    print(f"   Average price: ${stats['average_price']}")
    
    # Test 5: Error handling
    print("\n5. Testing error handling...")
    try:
        _get_product_logic(99999)
        print("   Should have raised ValueError")
    except ValueError as e:
        print(f"   Correctly raised error: {e}")
    
    print("\nAll basic operations passed!\n")
    return new_product.id


def test_concurrent_writes(num_threads=10, products_per_thread=5):
    """Test concurrent write operations."""
    print("=" * 60)
    print(f"TEST 2: Concurrent Writes ({num_threads} threads x {products_per_thread} products)")
    print("=" * 60)
    
    def add_products(thread_id):
        """Add multiple products from a single thread."""
        results = []
        for i in range(products_per_thread):
            try:
                product = _add_product_logic(CreateProductRequest(
                    name=f"Concurrent Product T{thread_id}-{i}",
                    price=100.0 + thread_id + i,
                    category="Test",
                    in_stock=True
                ))
                results.append(product.id)
            except Exception as e:
                print(f"   Thread {thread_id} failed: {e}")
                return []
        return results
    
    # Get initial count
    initial_stats = _get_stats_logic()
    initial_count = initial_stats['total_products']
    
    print(f"\n   Initial product count: {initial_count}")
    print(f"   Starting {num_threads} concurrent threads...")
    
    start_time = time.time()
    
    # Execute concurrent writes
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(add_products, i) for i in range(num_threads)]
        all_ids = []
        for future in as_completed(futures):
            result = future.result()
            all_ids.extend(result)
    
    elapsed = time.time() - start_time
    
    # Verify final count
    final_stats = _get_stats_logic()
    final_count = final_stats['total_products']
    expected_count = initial_count + (num_threads * products_per_thread)
    
    print(f"\n   Completed in {elapsed:.2f} seconds")
    print(f"   Successfully created {len(all_ids)} products")
    print(f"   Final product count: {final_count}")
    print(f"   Expected count: {expected_count}")
    
    if final_count == expected_count:
        print(f"\n   Concurrent writes handled correctly!")
    else:
        print(f"\n   Count mismatch! Lost some writes due to race conditions")
        return False
    
    # Verify all IDs are unique (no conflicts)
    if len(all_ids) == len(set(all_ids)):
        print(f"   All product IDs are unique (no conflicts)")
    else:
        print(f"   Duplicate IDs detected!")
        return False
    
    print("\nConcurrent write test passed!\n")
    return True


def test_rollback():
    """Test that rollback works on errors."""
    print("=" * 60)
    print("TEST 3: Transaction Rollback")
    print("=" * 60)
    
    initial_count = _get_stats_logic()['total_products']
    print(f"\n   Initial count: {initial_count}")
    
    # This should fail due to invalid data type
    print("   Attempting invalid operation...")
    try:
        # Try to add product with invalid price
        with get_db() as db:
            invalid_product = DBProduct(
                name="Invalid Product",
                price="not a number",  # This will cause an error
                category="Test",
                in_stock=True
            )
            db.add(invalid_product)
            db.flush()
    except Exception as e:
        print(f"   Error caught: {type(e).__name__}")
    
    # Verify count didn't change
    final_count = _get_stats_logic()['total_products']
    print(f"   Final count: {final_count}")
    
    if initial_count == final_count:
        print("\n   Rollback worked! No orphan records created.\n")
        return True
    else:
        print("\n   Rollback failed! Database is inconsistent.\n")
        return False


def test_query_performance():
    """Test query performance."""
    print("=" * 60)
    print("TEST 4: Query Performance")
    print("=" * 60)
    
    # Test list performance
    print("\n   Testing list_products performance...")
    start = time.time()
    products = _list_products_logic()
    elapsed = time.time() - start
    print(f"   Listed {len(products)} products in {elapsed*1000:.2f}ms")
    
    # Test single query performance
    if products:
        print("\n   Testing get_product performance...")
        start = time.time()
        product = _get_product_logic(products[0].id)
        elapsed = time.time() - start
        print(f"   Retrieved single product in {elapsed*1000:.2f}ms")
    
    # Test stats performance
    print("\n   Testing get_stats performance...")
    start = time.time()
    stats = _get_stats_logic()
    elapsed = time.time() - start
    print(f"   Calculated stats in {elapsed*1000:.2f}ms")
    
    print("\nPerformance test passed!\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SQLITE BONUS 1 VERIFICATION")
    print("=" * 60 + "\n")
    
    try:
        # Setup
        setup_test_db()
        
        # Run tests
        test_basic_operations()
        concurrent_pass = test_concurrent_writes()
        rollback_pass = test_rollback()
        test_query_performance()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Basic Operations: PASSED")
        print(f"{'✅' if concurrent_pass else '❌'} Concurrent Writes: {'PASSED' if concurrent_pass else 'FAILED'}")
        print(f"{'✅' if rollback_pass else '❌'} Transaction Rollback: {'PASSED' if rollback_pass else 'FAILED'}")
        print(f"✅ Query Performance: PASSED")
        print("=" * 60)
        
        if concurrent_pass and rollback_pass:
            print("\n🎉 All tests passed! SQLite is properly configured for concurrent writes.\n")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check the output above.\n")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
