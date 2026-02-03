import sys
import os
import contextlib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import StructuredTool

# --- PATH SETUP (Exact same as before) ---
current_file = os.path.abspath(__file__)
agent_dir = os.path.dirname(current_file)
src_dir = os.path.dirname(agent_dir)
project_root = os.path.dirname(src_dir)
server_script = os.path.join(src_dir, "mcp", "mcp_server.py")

env = os.environ.copy()
env["PYTHONPATH"] = project_root

server_params = StdioServerParameters(
    command=sys.executable, args=[server_script], env=env
)


class MCPConnection:
    """
    Keeps one connection open for the entire lifetime of the agent.
    """

    def __init__(self):
        self.exit_stack = contextlib.AsyncExitStack()
        self.session = None

    async def connect(self):
        """Start the server and establish the session."""
        print("Connecting to MCP Server...")
        # We manually enter the context managers so they stay open!
        read, write = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self.session.initialize()
        print("Connected!")

    async def close(self):
        """Close the connection and kill the server."""
        print("Disconnecting...")
        await self.exit_stack.aclose()

    async def run_tool(self, name: str, args: dict) -> str:
        """Run a tool using the existing open session."""
        if not self.session:
            return "Error: Agent is not connected to MCP server."

        try:
            result = await self.session.call_tool(name, args)
            if hasattr(result, "isError") and result.isError:
                return f"Error: {result.content[0].text}"
            if not result.content:
                return "Success"
            return result.content[0].text
        except Exception as e:
            return f"System Error: {str(e)}"


# Global instance (so tools can find it)
global_mcp = MCPConnection()




async def get_langchain_tools():
    if not global_mcp.session:
        await global_mcp.connect()

    mcp_tools = await global_mcp.session.list_tools()

    langchain_tools = []
    for t in mcp_tools.tools:
        def make_wrapper(tool_name):
            async def wrapper(**kwargs):
                return await global_mcp.run_tool(tool_name, kwargs)
            return wrapper

        lc_tool = StructuredTool.from_function(
            func=None, 
            coroutine=make_wrapper(t.name), 
            name=t.name, 
            description=t.description,
            args_schema=t.inputSchema if hasattr(t, 'inputSchema') else None
        )
        langchain_tools.append(lc_tool)

    return langchain_tools
