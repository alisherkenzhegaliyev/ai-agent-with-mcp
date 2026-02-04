# AI Agent with MCP

A production-ready LangGraph agent that integrates with a Model Context Protocol (MCP) server for product management, featuring FastAPI endpoints, Docker containerization, and comprehensive testing.

## Architecture

```
src/
├── agent/              # LangGraph agent implementation
│   ├── agent.py            # Agent orchestration with StateGraph
│   ├── mock_llm.py         # Mock LLM with NLU (supports product ID & name discounts)
│   ├── tools_local.py      # Local tools (calculator, formatter)
│   └── tools_remote.py     # MCP client connection via stdio
├── producer_mcp/       # MCP Server
│   └── mcp_server.py       # FastMCP server with 4 tools + SQLite backend
├── data/               # Data models and persistence
│   ├── product.py          # Pydantic models
│   ├── db.py               # SQLAlchemy models + connection pooling
│   ├── migrations.py       # Database migrations
│   ├── products.db         # SQLite database (Bonus 1)
│   └── products.json       # Initial data seed
├── app/                # FastAPI application
│   ├── main.py             # API endpoints + lifespan events
│   └── root.py             # Interactive HTML chat interface
└── config/             # Configuration
    └── logging.py          # Centralized logging setup

tests/
├── test_agent_flow.py      # Agent intent recognition tests
├── test_mcp_tools.py       # MCP tool functionality tests
├── test_api.py             # FastAPI endpoint tests
└── test_sqlite_bonus.py    # SQLite concurrency + performance tests
```

## Features

### MCP Server 
- FastMCP with `@mcp.tool` decorators
- 4 tools: `list_products`, `get_product`, `add_product`, `get_stats`
- Communication via stdio transport
- SQLite backend with SQLAlchemy ORM
- Error handling with proper exceptions

### LangGraph Agent
- Connects to MCP server via stdio
- Uses all 4 MCP tools dynamically
- Custom tools: `calculator` (math operations), `formatter` (text formatting)
- Mock LLM with regex-based NLU (no API keys needed)
- Smart intent detection: distinguishes product-specific discounts from generic calculations

### FastAPI + Docker 
- `POST /api/v1/agent/query` endpoint with proper request/response models
- Interactive HTML chat interface at root (`/`)
- Dockerfile with Python 3.11-slim
- docker-compose.yml with volume mounts for persistence
- Runs successfully with `docker-compose up`

### SQLite Persistence
- SQLAlchemy ORM with Product model
- Connection pooling for concurrent writes (pool_size=10, timeout=30s)
- Context managers with automatic commit/rollback
- Database migrations support
- Empty database handling with user-friendly messages
- Comprehensive test suite for concurrency and performance


## Quick Start

### Option 1: Docker (Recommended)

```bash
# Build and start the container
make build && make up

# Or manually:
docker-compose up --build

# Access the chat interface
open http://localhost:8000

# API endpoint
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "show all products"}'
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn src.app.main:app --reload

# Or run the terminal chat interface
python -m src.agent.agent
```

## Testing

```bash
# Run all tests
make test

# Or manually:
pytest tests/ -v

# Run specific test files
pytest tests/test_agent_flow.py -v        # Agent intent recognition
pytest tests/test_mcp_tools.py -v         # MCP tool operations
pytest tests/test_api.py -v               # FastAPI endpoints
pytest tests/test_sqlite_bonus.py -v      # SQLite concurrency & performance
```

## Usage Examples

<img width="1053" height="879" alt="Screenshot 2026-02-04 at 17 45 59" src="https://github.com/user-attachments/assets/9fe2e241-d76f-4c58-b3ec-37f25b9cd0d3" />
<img width="1061" height="878" alt="Screenshot 2026-02-04 at 17 46 07" src="https://github.com/user-attachments/assets/5f868aa1-5cf2-4e5d-927a-656a194b38ef" />


### Chat Interface (Browser)
1. Open http://localhost:8000 in your browser
2. Type queries naturally:
   - "show me all products"
   - "what's the average price?"
   - "add product: Mouse, price 1500, category Electronics"
   - "calculate 15% discount on 100" (generic calculation)
   - "make 15% discount on id 1" (product-specific discount)
   - "make 15% discount on Mouse" (discount by product name)

### API Endpoint (cURL)
<img width="917" height="488" alt="Screenshot 2026-02-04 at 17 46 46" src="https://github.com/user-attachments/assets/40a15dc0-130f-49d2-94e8-ec08bdcf8be4" />

```bash
# List all products
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "show all products"}'

# Get statistics
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "what is the average price?"}'

# Add a product
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "add product: Keyboard, price 2500, category Electronics"}'

# Calculate discount
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "calculate 20% discount on 5000"}'
```

### Terminal Chat (Local)

```bash
python -m src.agent.agent

# Then interact naturally:
YOU: show me all products
ASSISTANT: Here are all products: ...

YOU: what's the total count?
ASSISTANT: Total products: 3, Average price: 2500.00
```

## Makefile Commands

```bash
make build          # Build Docker image
make build-fresh    # Clean everything and rebuild from scratch
make up             # Start containers (attached)
make up-d           # Start containers (detached)
make down           # Stop containers
make restart        # Restart containers
make logs           # Show container logs
make test           # Run all pytest tests
make test-sqlite    # Run SQLite-specific tests
make clean          # Remove containers, volumes, and images
make clean-all      # Complete cleanup (includes DB and cache files)
```

## Configuration

### Environment Variables
- `PORT`: FastAPI server port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

### Data Persistence
- Products stored in SQLite database (`src/data/products.db`)
- Volume mounted in Docker for persistence across restarts
- Connection pooling handles concurrent writes safely
- Initial seed data from `products.json`

## Dependencies

Core packages:
- `fastapi>=0.115.0` - Web framework
- `uvicorn[standard]>=0.32.1` - ASGI server
- `langchain-core>=0.3.33` - LangChain core functionality
- `langgraph>=0.2.70` - Agent orchestration with StateGraph
- `mcp>=1.0.0` - MCP protocol
- `fastmcp>=2.0.0` - FastMCP server framework
- `sqlalchemy>=2.0.0` - ORM for SQLite persistence
- `pydantic>=2.10.4` - Data validation
- `pytest>=9.0.0` - Testing framework


## Troubleshooting

### Docker Issues
```bash
# Clean rebuild
make clean-all && make build && make up

# Check logs
docker-compose logs -f
```

### Port Already in Use
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### MCP Connection Issues
- Ensure MCP server starts before agent initialization
- Check logs for stdio connection errors
- Verify tools are registered: look for "Agent initialized with X tools"

### Database Issues
<img width="834" height="75" alt="Screenshot 2026-02-04 at 17 47 09" src="https://github.com/user-attachments/assets/49250f16-3e3d-48e3-beaa-c87d8e5944ae" />

```bash
# Reset database
make clean-all  # Removes products.db and rebuilds from scratch

# Check database integrity
sqlite3 src/data/products.db "SELECT * FROM products;"
```
