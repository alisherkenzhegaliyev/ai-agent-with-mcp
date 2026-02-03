from langchain_core.tools import tool


@tool
def calculator(operation: str, a: float, b: float) -> float:
    """
    Perform basic arithmetic operations.
    Allowed operations: 'add', 'subtract', 'multiply', 'divide'.
    """
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            return "Error: Division by zero"
        return a / b
    else:
        return f"Error: Unknown operation '{operation}'"


@tool
def formatter(text: str, style: str) -> str:
    """
    Format text in a specific style.
    Allowed styles: 'uppercase', 'lowercase', 'title'.
    """
    if style == "uppercase":
        return text.upper()
    elif style == "lowercase":
        return text.lower()
    elif style == "title":
        return text.title()
    else:
        return text
