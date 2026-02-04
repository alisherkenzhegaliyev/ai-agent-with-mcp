from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from src.agent.agent import build_agent
from src.agent.tools_remote import global_mcp
from langchain_core.messages import HumanMessage
from contextlib import asynccontextmanager
from typing import List, Optional
from src.app.root import root

class AgentQueryRequest(BaseModel):
    query: str


class AgentQueryResponse(BaseModel):
    query: str
    response: str
    tool_calls: List[str]


# Global agent instance
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Build the agent
    global agent
    agent = await build_agent()
    yield
    # Shutdown: Close MCP connection
    await global_mcp.close()


app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
def read_root():
    return root()

@app.post("/api/v1/agent/query", response_model=AgentQueryResponse)
async def post(request: AgentQueryRequest):
    """Execute agent query and return response."""
    if not agent:
        return {
            "query": request.query,
            "response": "Error: Agent not initialized",
            "tool_calls": []
        }
    
    # Create initial state with user message
    initial_state = {"messages": [HumanMessage(content=request.query)]}
    
    # Track tool calls and collect response
    tool_calls_used = []
    final_response = ""
    
    # Stream through the agent
    async for event in agent.astream(initial_state):
        for key, value in event.items():
            if key == "agent":
                msg = value["messages"][0]
                # Track tool calls
                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_calls_used.append(tool_call["name"])
                # Get final text response
                elif msg.content:
                    final_response = msg.content
    
    return {
        "query": request.query,
        "response": final_response,
        "tool_calls": tool_calls_used
    }
