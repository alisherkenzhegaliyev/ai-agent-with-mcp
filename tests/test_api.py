import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


@pytest.fixture
def mock_agent():
    """Create a mock agent that simulates agent behavior."""
    mock = AsyncMock()
    
    # Simulate agent streaming events
    async def mock_astream(state):
        # Simulate agent deciding to call a tool
        tool_call_msg = AIMessage(
            content="",
            tool_calls=[{"name": "list_products", "args": {}, "id": "call_123"}]
        )
        yield {"agent": {"messages": [tool_call_msg]}}
        
        # Simulate final response
        final_msg = AIMessage(content="Here are the products...")
        yield {"agent": {"messages": [final_msg]}}
    
    mock.astream = mock_astream
    return mock


@pytest.fixture
def client(mock_agent):
    """Create a test client with mocked agent."""
    with patch('src.app.main.build_agent', new_callable=AsyncMock) as mock_build:
        with patch('src.app.main.global_mcp') as mock_mcp:
            # Setup mocks
            mock_build.return_value = mock_agent
            mock_mcp.close = AsyncMock()
            
            # Import after patching
            from src.app.main import app
            
            with TestClient(app) as test_client:
                yield test_client


def test_root_endpoint_returns_html(client):
    """Test that root endpoint returns HTML page."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Product Management Agent" in response.text
    assert "chat-container" in response.text


def test_query_endpoint_success(client):
    """Test successful query to agent."""
    response = client.post(
        "/api/v1/agent/query",
        json={"query": "show all products"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "query" in data
    assert "response" in data
    assert "tool_calls" in data
    
    assert data["query"] == "show all products"
    assert isinstance(data["response"], str)
    assert isinstance(data["tool_calls"], list)


def test_query_endpoint_with_tool_calls(client):
    """Test that tool calls are tracked."""
    response = client.post(
        "/api/v1/agent/query",
        json={"query": "list all products"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "list_products" in data["tool_calls"]


def test_query_endpoint_invalid_request(client):
    """Test validation error for invalid request."""
    response = client.post(
        "/api/v1/agent/query",
        json={"invalid_field": "test"}
    )
    
    assert response.status_code == 422  # Validation error


def test_query_endpoint_empty_query(client):
    """Test handling of empty query."""
    response = client.post(
        "/api/v1/agent/query",
        json={"query": ""}
    )
    
    # Should still process, even if empty
    assert response.status_code in [200, 422]


def test_query_endpoint_various_queries(client):
    """Test different types of queries."""
    queries = [
        "show all products",
        "what's the average price?",
        "add product: Mouse, price 1500, category Electronics",
    ]
    
    for query in queries:
        response = client.post(
            "/api/v1/agent/query",
            json={"query": query}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == query
        assert "response" in data
        assert "tool_calls" in data


def test_response_format_compliance(client):
    """Test that response follows the expected schema."""
    response = client.post(
        "/api/v1/agent/query",
        json={"query": "test query"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all required fields exist
    required_fields = ["query", "response", "tool_calls"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Check types
    assert isinstance(data["query"], str)
    assert isinstance(data["response"], str)
    assert isinstance(data["tool_calls"], list)
    
    # Check tool_calls contains only strings
    for tool in data["tool_calls"]:
        assert isinstance(tool, str)


def test_concurrent_requests(client):
    """Test handling multiple concurrent requests."""
    import concurrent.futures
    
    def make_request(query):
        return client.post(
            "/api/v1/agent/query",
            json={"query": query}
        )
    
    queries = [f"query {i}" for i in range(5)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, q) for q in queries]
        responses = [f.result() for f in futures]
    
    # All requests should succeed
    for response in responses:
        assert response.status_code == 200


def test_long_query_handling(client):
    """Test handling of very long queries."""
    long_query = "show products " * 100  # Very long query
    
    response = client.post(
        "/api/v1/agent/query",
        json={"query": long_query}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == long_query


def test_special_characters_in_query(client):
    """Test handling of special characters."""
    special_query = "show products with price > $100 & category = 'Electronics'"
    
    response = client.post(
        "/api/v1/agent/query",
        json={"query": special_query}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == special_query
