# AI Agent with MCP

A production-ready LangGraph agent that integrates with a Model Context Protocol (MCP) server for product management, featuring FastAPI endpoints, Docker containerization, and comprehensive testing.

## 🏗️ Architecture

```
src/
├── agent/          # LangGraph agent implementation
│   ├── agent.py           # Agent orchestration with StateGraph
│   ├── mock_llm.py        # Mock LLM with natural language understanding
│   ├── tools_local.py     # Local tools (calculator, formatter)
│   └── tools_remote.py    # MCP client connection via stdio
├── mcp/            # MCP Server
│   └── mcp_server.py      # FastMCP server with 4 product management tools
├── data/           # Data models and storage
│   ├── product.py         # Pydantic models
│   └── products.json      # Product database
└── app/            # FastAPI application
    ├── main.py            # API endpoints and agent integration
    └── root.py            # HTML chat interface
```

## ✨ Features

### MCP Server 
- ✅ FastMCP with `@mcp.tool` decorators
- ✅ 4 tools: `list_products`, `get_product`, `add_product`, `get_stats`
- ✅ Communication via stdio transport
- ✅ Error handling with proper exceptions

### LangGraph Agent 
- ✅ Connects to MCP server via stdio
- ✅ Uses all 4 MCP tools dynamically
- ✅ Custom tools: `calculator` (math operations), `formatter` (text formatting)
- ✅ Mock LLM with regex-based natural language understanding (no API keys needed)

### FastAPI + Docker
- ✅ `POST /api/v1/agent/query` endpoint with proper request/response models
- ✅ Interactive HTML chat interface at root (`/`)
- ✅ Dockerfile with Python 3.11-slim
- ✅ docker-compose.yml with volume mounts
- ✅ Runs successfully with `docker-compose up`


## 🚀 Quick Start

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

## 🧪 Testing

```bash
# Run all tests
make test

# Or manually:
pytest tests/ -v

# Run specific test files
pytest tests/test_agent_flow.py -v
pytest tests/test_mcp_tools.py -v
pytest tests/test_api.py -v
```

## 📝 Usage Examples

### Chat Interface (Browser)
1. Open http://localhost:8000 in your browser
2. Type queries naturally:
   - "show me all products"
   - "what's the average price?"
   - "add product: Mouse, price 1500, category Electronics"
   - "calculate 15% discount on Laptop"

### API Endpoint (cURL)

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

## 🛠️ Makefile Commands

```bash
make build      # Build Docker image
make up         # Start containers
make down       # Stop containers
make restart    # Restart containers
make test       # Run all tests
make clean      # Remove containers and volumes
```

## 🔧 Configuration

### Environment Variables
- `PORT`: FastAPI server port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

### Data Persistence
- Products stored in `src/data/products.json`
- Volume mounted in Docker for persistence
- Changes persist across container restarts

## 📦 Dependencies

Core packages:
- `fastapi>=0.115.0` - Web framework
- `uvicorn[standard]>=0.32.1` - ASGI server
- `langchain-core>=0.3.33` - LangChain core functionality
- `langgraph>=0.2.70` - Agent orchestration
- `mcp>=1.0.0` - MCP protocol
- `fastmcp>=2.0.0` - FastMCP server framework
- `pydantic>=2.10.4` - Data validation
- `pytest>=9.0.0` - Testing framework


## 🐛 Troubleshooting

### Docker Issues
```bash
# Clean rebuild
make clean && make build && make up

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