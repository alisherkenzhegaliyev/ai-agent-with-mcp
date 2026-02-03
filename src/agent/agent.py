import sys
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import tool

# We need to tell the client how to launch your server
server_params = StdioServerParameters(
    command=sys.executable,  # Uses the same Python as your venv
    args=["src/mcp_server.py"],  # The script to run
    env=None,
)


async def get_remote_tools():
    """
    Connects to the MCP server and returns a list of callable tools.
    """
    # We use a context manager to keep the connection alive
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Initialize the connection
            await session.initialize()

            # 2. Ask the server: "What tools do you have?"
            tools_list = await session.list_tools()

            print(f"✅ Connected to MCP Server. Found {len(tools_list.tools)} tools.")

            # TODO: We need to convert these 'MCP Tools' into 'LangChain Tools'
            # For now, let's just print them to prove it works.
            for t in tools_list.tools:
                print(f" - {t.name}: {t.description}")


# Quick test to verify connection
if __name__ == "__main__":
    asyncio.run(get_remote_tools())
