import pytest
from src.agent.mock_llm import MockChatModel
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.outputs import ChatResult


@pytest.fixture
def mock_llm():
    """Create a fresh MockChatModel instance for each test."""
    return MockChatModel()


# --- Test Intent Recognition ---


def test_list_products_intent(mock_llm):
    """It should recognize list products intent with various phrases."""
    test_cases = [
        "show me all products",
        "list all products",
        "what products do you have",
        "display all items",
        "view the catalog",
    ]
    
    for query in test_cases:
        message = HumanMessage(content=query)
        result = mock_llm._generate([message])
        
        assert len(result.generations) == 1
        ai_message = result.generations[0].message
        assert ai_message.tool_calls
        assert ai_message.tool_calls[0]["name"] == "list_products"


def test_get_stats_intent(mock_llm):
    """It should recognize statistics intent."""
    test_cases = [
        "what's the average price?",
        "calculate the average price",
        "give me statistics on prices",
        "what is the mean cost",
        "show me the average product price",
    ]
    
    for query in test_cases:
        message = HumanMessage(content=query)
        result = mock_llm._generate([message])
        
        ai_message = result.generations[0].message
        assert ai_message.tool_calls, f"No tool calls for query: {query}"
        assert ai_message.tool_calls[0]["name"] == "get_stats", f"Wrong tool for query '{query}': {ai_message.tool_calls[0]['name']}"


def test_add_product_intent(mock_llm):
    """It should extract product details from natural language."""
    queries = [
        "add product: Mouse, price 1500, category Electronics",
        "create new item: Keyboard, price 2500, category Accessories",
    ]
    
    for query in queries:
        message = HumanMessage(content=query)
        result = mock_llm._generate([message])
        
        ai_message = result.generations[0].message
        assert ai_message.tool_calls
        assert ai_message.tool_calls[0]["name"] == "add_product"
        
        args = ai_message.tool_calls[0]["args"]
        assert "name" in args
        assert "price" in args
        assert "category" in args
        assert args["in_stock"] is True


def test_calculator_intent(mock_llm):
    """It should recognize calculator operations."""
    message = HumanMessage(content="calculate 15% discount on 100")
    result = mock_llm._generate([message])
    
    ai_message = result.generations[0].message
    assert ai_message.tool_calls
    assert ai_message.tool_calls[0]["name"] == "calculator"
    
    args = ai_message.tool_calls[0]["args"]
    assert args["operation"] == "multiply"
    assert args["a"] == 100
    assert abs(args["b"] - 0.85) < 0.01  # 1 - 0.15


def test_get_product_by_id_intent(mock_llm):
    """It should extract product ID from various formats."""
    test_cases = [
        ("fetch product 1", 1),
        ("find product with id 5", 5),
        ("get product #3", 3),
        ("show details of id 10", 10),
    ]
    
    for query, expected_id in test_cases:
        message = HumanMessage(content=query)
        result = mock_llm._generate([message])
        
        ai_message = result.generations[0].message
        assert ai_message.tool_calls, f"No tool calls for query: {query}"
        assert ai_message.tool_calls[0]["name"] == "get_product", f"Wrong tool for query '{query}': {ai_message.tool_calls[0]['name']}"
        assert ai_message.tool_calls[0]["args"]["product_id"] == expected_id


def test_discount_on_product_name(mock_llm):
    """It should handle discount on product name by listing products first."""
    message = HumanMessage(content="calculate 15% discount on keyboard")
    result = mock_llm._generate([message])
    
    ai_message = result.generations[0].message
    assert ai_message.tool_calls
    # Should call list_products to find the product
    assert ai_message.tool_calls[0]["name"] == "list_products"
    
    # Check that discount context is stored
    assert "discount_calc" in mock_llm._context
    assert mock_llm._context["discount_calc"]["discount"] == 15
    assert mock_llm._context["discount_calc"]["product_name"] == "keyboard"


# --- Test Response Formatting ---


def test_format_product_list(mock_llm):
    """It should format product list responses nicely."""
    products_json = """[
        {"id": 1, "name": "Laptop", "price": 1000, "category": "Electronics", "in_stock": true},
        {"id": 2, "name": "Mouse", "price": 50, "category": "Accessories", "in_stock": true}
    ]"""
    
    result = mock_llm._format_json_output(products_json)
    
    assert "Here are the products I found:" in result
    assert "Laptop" in result
    assert "$1000" in result
    assert "Mouse" in result
    assert "Electronics" in result


def test_format_stats(mock_llm):
    """It should format statistics responses."""
    stats_json = '{"total_products": 5, "average_price": 1250.5}'
    
    result = mock_llm._format_json_output(stats_json)
    
    assert "5 products" in result
    assert "1250.5" in result


def test_format_add_product_success(mock_llm):
    """It should format add product success message."""
    product_json = '{"id": 10, "name": "Keyboard", "price": 2500, "category": "Electronics", "in_stock": true}'
    
    result = mock_llm._format_json_output(product_json)
    
    assert "Successfully added" in result
    assert "Keyboard" in result
    assert "ID: 10" in result


def test_format_discount_calculation(mock_llm):
    """It should calculate and format discount on product name."""
    # Set up discount context
    mock_llm._context["discount_calc"] = {
        "discount": 15,
        "product_name": "keyboard"
    }
    
    products_json = """[
        {"id": 1, "name": "Keyboard", "price": 2500, "category": "Electronics", "in_stock": true},
        {"id": 2, "name": "Mouse", "price": 50, "category": "Accessories", "in_stock": true}
    ]"""
    
    result = mock_llm._format_json_output(products_json)
    
    assert "Keyboard" in result
    assert "$2500" in result
    assert "15%" in result
    assert "$2125" in result  # 2500 * 0.85


def test_format_discount_product_not_found(mock_llm):
    """It should handle case when product name doesn't match."""
    mock_llm._context["discount_calc"] = {
        "discount": 15,
        "product_name": "nonexistent"
    }
    
    products_json = """[
        {"id": 1, "name": "Keyboard", "price": 2500, "category": "Electronics", "in_stock": true}
    ]"""
    
    result = mock_llm._format_json_output(products_json)
    
    assert "couldn't find" in result.lower()
    assert "nonexistent" in result


def test_format_calculator_result(mock_llm):
    """It should format calculator results."""
    result = mock_llm._format_json_output("42.5")
    assert "result" in result.lower()
    assert "42.5" in result


def test_unknown_query(mock_llm):
    """It should handle unknown queries gracefully."""
    message = HumanMessage(content="tell me a joke")
    result = mock_llm._generate([message])
    
    ai_message = result.generations[0].message
    assert not ai_message.tool_calls
    assert "don't know" in ai_message.content.lower()


# --- Test Helper Methods ---


def test_extract_product_id_various_formats(mock_llm):
    """It should extract product IDs from various text formats."""
    test_cases = [
        ("product 5", 5),
        ("id 123", 123),
        ("product with id 42", 42),
        ("#99", 99),
    ]
    
    for text, expected_id in test_cases:
        result = mock_llm._extract_product_id(text)
        assert result == expected_id


def test_extract_product_id_not_found(mock_llm):
    """It should return None when no ID is found."""
    result = mock_llm._extract_product_id("show all products")
    assert result is None


def test_match_calculator_operations(mock_llm):
    """It should match various calculator operations."""
    test_cases = [
        ("multiply 10 by 5", {"operation": "multiply", "a": 10.0, "b": 5.0}),
        ("add 100 plus 50", {"operation": "add", "a": 100.0, "b": 50.0}),
        ("subtract 75 minus 25", {"operation": "subtract", "a": 75.0, "b": 25.0}),
        ("divide 100 by 4", {"operation": "divide", "a": 100.0, "b": 4.0}),
    ]
    
    for query, expected in test_cases:
        result = mock_llm._match_calculator(query)
        assert result is not None
        assert result["operation"] == expected["operation"]
        assert result["a"] == expected["a"]
        assert result["b"] == expected["b"]


def test_match_add_product_variations(mock_llm):
    """It should extract product info from various formats."""
    query = "add product: Mouse, price 1500, category Electronics"
    result = mock_llm._match_add_product(query)
    
    assert result is not None
    assert "mouse" in result["name"].lower()
    assert result["price"] == 1500.0
    assert "electronics" in result["category"].lower()


def test_match_intent_with_word_boundaries(mock_llm):
    """It should use word boundaries to avoid substring matches."""
    # "discount" contains "count" but should not match stats intent
    text = "calculate discount on product"
    
    # Should NOT match stats intent (which has "count" keyword)
    stats_match = mock_llm._match_intent(
        text,
        ["average", "mean", "stats", "statistics", "total", "count", "how many"],
        ["price", "cost", "product", "item"]
    )
    assert not stats_match  # "count" in "discount" should not match


# --- Test Tool Response Handling ---


def test_tool_response_processing(mock_llm):
    """It should process tool responses and format them."""
    # Simulate a complete flow
    user_message = HumanMessage(content="show all products")
    
    # Phase 1: Generate tool call
    result1 = mock_llm._generate([user_message])
    ai_message = result1.generations[0].message
    
    assert ai_message.tool_calls
    assert ai_message.tool_calls[0]["name"] == "list_products"
    
    # Phase 2: Process tool output
    tool_output = """[
        {"id": 1, "name": "Test Product", "price": 100, "category": "Test", "in_stock": true}
    ]"""
    tool_message = ToolMessage(content=tool_output, tool_call_id="test_123")
    
    result2 = mock_llm._generate([user_message, ai_message, tool_message])
    final_response = result2.generations[0].message
    
    assert not final_response.tool_calls
    assert "Test Product" in final_response.content
    assert "$100" in final_response.content


def test_llm_type_property(mock_llm):
    """It should return correct LLM type."""
    assert mock_llm._llm_type == "mock-chat-model"


def test_context_persistence(mock_llm):
    """It should maintain context across calls."""
    # First call stores context
    message1 = HumanMessage(content="calculate 20% discount on laptop")
    mock_llm._generate([message1])
    
    assert "discount_calc" in mock_llm._context
    assert mock_llm._context["discount_calc"]["discount"] == 20
    
    # Context should be used in next call
    products_json = """[{"id": 1, "name": "Laptop", "price": 1000, "category": "Tech", "in_stock": true}]"""
    result = mock_llm._format_json_output(products_json)
    
    assert "20" in result and "%" in result  # Accept both "20%" and "20.0%"
    assert "$800" in result  # 1000 * 0.8
    
    # Context should be cleared after use
    assert "discount_calc" not in mock_llm._context
