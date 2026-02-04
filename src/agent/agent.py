import asyncio
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage


from src.agent.tools_local import calculator, formatter
from src.agent.tools_remote import get_langchain_tools
from src.agent.mock_llm import MockChatModel
from src.config.logging import get_logger

logger = get_logger(__name__)


async def build_agent():
    """
    Constructs the compiled LangGraph agent with all tools loaded.
    """
    logger.info("Building LangGraph agent...")
    
    # 1. Load Tools
    # combine the local Python tools with the remote MCP tools
    remote_tools = await get_langchain_tools()
    local_tools = [calculator, formatter]
    all_tools = local_tools + remote_tools

    logger.info(f"Agent initialized with {len(all_tools)} tools:")
    for t in all_tools:
        logger.info(f"  - {t.name}")
        print(f"  - {t.name}")

    # 2. Initialize the Brain (Mock LLM)
    # bind the tools to the LLM so it knows they exist
    llm = MockChatModel()
    llm_with_tools = llm

    # 3. Define the Nodes

    def agent_node(state: MessagesState):
        """The 'Brain' node: Decides what to do next."""
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # The 'Action' node: Actually runs the tools
    tool_node = ToolNode(all_tools)

    # 4. Build the Graph
    workflow = StateGraph(MessagesState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("agent")

    # 5. Define Edges (The Flow)
    # If the agent returned a tool call -> Go to 'tools'
    # If the agent returned just text -> Go to END
    workflow.add_conditional_edges(
        "agent",
        lambda state: "tools" if state["messages"][-1].tool_calls else END,
        {"tools": "tools", END: END},
    )

    # When tools finish, go back to the agent to read the results
    workflow.add_edge("tools", "agent")

    return workflow.compile()


# Import the global instance we created
from src.agent.tools_remote import get_langchain_tools, global_mcp

# ... (keep build_agent and imports the same) ...


async def run_chat():
    try:
        # 1. Build the agent (this triggers the connection via get_langchain_tools)
        agent = await build_agent()

        print("\n" + "=" * 60)
        print("PRODUCT MANAGEMENT ASSISTANT")
        print("=" * 60)
        print("\nType your questions naturally. Examples:")
        print("  • 'show me all products'")
        print("  • 'what's the average price?'")
        print("  • 'add product: Keyboard, price 2500, category Electronics'")
        print("  • 'calculate 15% discount on keyboard'")
        print("\nType 'exit' or 'quit' to stop.\n")
        print("=" * 60 + "\n")

        while True:
            # Get user input
            try:
                user_input = input("YOU: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nGoodbye!")
                break

            # Exit conditions
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print("\nGoodbye")
                break

            # Process the user's message
            initial_state = {"messages": [HumanMessage(content=user_input)]}

            async for event in agent.astream(initial_state):
                for key, value in event.items():
                    if key == "agent":
                        msg = value["messages"][0]
                        if msg.tool_calls:
                            print(
                                f"Calling: {msg.tool_calls[0]['name']}({msg.tool_calls[0]['args']})"
                            )
                        elif msg.content:
                            print(f"\nAGENT: {msg.content}\n")
                    elif key == "tools":
                        pass  # Tool execution happens silently

    finally:
        # 2. CRITICAL: Always close the connection at the end
        await global_mcp.close()


if __name__ == "__main__":
    asyncio.run(run_chat())
