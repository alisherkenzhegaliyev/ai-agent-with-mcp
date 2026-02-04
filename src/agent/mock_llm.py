from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from typing import Any, List, Optional
import json
import re


class MockChatModel(BaseChatModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._context = {}  # Store context between calls
    
    def _generate(
        self, messages: List[Any], stop: Optional[List[str]] = None, **kwargs
    ) -> ChatResult:
        last_message = messages[-1]

        # --- PHASE 1: Decide to Call a Tool ---
        if isinstance(last_message, HumanMessage):
            text = last_message.content.lower()
            
            # Store the original query for context
            self._context['last_query'] = text

            # Intent: Get specific product by ID (check before list_products since it's more specific)
            product_id = self._extract_product_id(text)
            if product_id and any(
                word in text for word in ["get", "show", "fetch", "find", "details"]
            ):
                return self._create_tool_call("get_product", {"product_id": product_id})

            # Intent: Get statistics (check before list_products since it's more specific)
            if self._match_intent(
                text,
                ["average", "mean", "stats", "statistics", "total", "count", "how many"],
                ["price", "prices", "cost", "costs", "product", "products", "item", "items"],
            ):
                return self._create_tool_call("get_stats", {})

            # Intent: List products
            if self._match_intent(
                text,
                [
                    "list",
                    "show",
                    "display",
                    "get",
                    "what",
                    "all",
                    "view",
                    "see",
                ],
                ["product", "products", "item", "items", "catalog", "inventory"],
            ):
                return self._create_tool_call("list_products", {})

            # Intent: Add product (extract parameters from text)
            add_match = self._match_add_product(text)
            if add_match:
                return self._create_tool_call("add_product", add_match)

            # Intent: Calculate discount
            calc_match = self._match_calculator(text)
            if calc_match:
                return self._create_tool_call("calculator", calc_match)
            
            # Intent: Discount on product name (need to look up price first)
            discount_product = self._match_discount_on_product(text)
            if discount_product:
                # Store the discount context for later use
                self._context['discount_calc'] = discount_product
                return self._create_tool_call("list_products", {})

        # --- PHASE 2: React to Tool Output ---
        elif isinstance(last_message, ToolMessage):
            tool_output = last_message.content

            # Helper to format the output
            formatted_response = self._format_json_output(tool_output)
            return self._create_text_response(formatted_response)

        return self._create_text_response("I don't know how to handle that.")

    def _format_json_output(self, output: str) -> str:
        """Tries to parse JSON and make it readable."""
        try:
            data = json.loads(output)

            # Check if this was a discount calculation request
            if 'discount_calc' in self._context and isinstance(data, list):
                discount_info = self._context.pop('discount_calc')
                product_name = discount_info['product_name'].lower()
                discount_percent = discount_info['discount']
                
                # Find the product
                matching_product = None
                for item in data:
                    if product_name in item['name'].lower():
                        matching_product = item
                        break
                
                if matching_product:
                    original_price = matching_product['price']
                    discounted_price = original_price * (1 - discount_percent / 100)
                    return f"The {matching_product['name']} costs ${original_price}. With a {discount_percent}% discount, the price would be ${discounted_price:.2f}."
                else:
                    return f"I couldn't find a product matching '{discount_info['product_name']}' in the catalog."

            # Case 1: List of Products
            if isinstance(data, list) and len(data) > 0 and "name" in data[0]:
                lines = ["Here are the products I found:"]
                for item in data:
                    lines.append(
                        f"• {item['name']} (${item['price']}) - {item['category']}"
                    )
                return "\n".join(lines)

            # Case 2: Stats Dictionary
            if isinstance(data, dict) and "total_products" in data:
                return f"I found {data['total_products']} products with an average price of ${data['average_price']}."

            # Case 3: Single Product (Add Product Result)
            if isinstance(data, dict) and "id" in data:
                return f"Successfully added '{data['name']}' (ID: {data['id']}) to the catalog."

        except json.JSONDecodeError:
            pass

        # Fallback for simple strings (like calculator output)
        return f"The result is: {output}"

    def _create_tool_call(self, name, args):
        msg = AIMessage(
            content="", tool_calls=[{"name": name, "args": args, "id": "call_123"}]
        )
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def _create_text_response(self, text):
        msg = AIMessage(content=text)
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def _match_intent(
        self, text: str, action_keywords: List[str], entity_keywords: List[str]
    ) -> bool:
        """Check if text contains any action keyword AND any entity keyword."""
        # Use word boundaries to avoid substring matches (e.g., 'count' in 'discount')
        has_action = any(re.search(r'\b' + re.escape(keyword) + r'\b', text) for keyword in action_keywords)
        has_entity = any(re.search(r'\b' + re.escape(keyword) + r'\b', text) for keyword in entity_keywords)
        return has_action and has_entity

    def _extract_product_id(self, text: str) -> Optional[int]:
        """Extract product ID from text like 'product 1', 'ID 5', 'product with id 3'."""
        patterns = [
            r"product\s+(\d+)",
            r"id\s+(\d+)",
            r"product\s+with\s+id\s+(\d+)",
            r"#(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None

    def _match_add_product(self, text: str) -> Optional[dict]:
        """
        Extract product details from natural language like:
        - 'add product: Mouse, price 1500, category Electronics'
        - 'create new item Mouse for $1500 in Electronics'
        - 'add Mouse 1500 Electronics'
        """
        if not any(
            word in text
            for word in ["add", "create", "insert", "new", "register"]
        ):
            return None

        # Try to extract: name, price, category
        name, price, category = None, None, None

        # Extract price first (more reliable)
        price_match = re.search(r"(?:price|cost|for)\s*:?\s*\$?(\d+(?:\.\d+)?)", text)
        if price_match:
            price = float(price_match.group(1))

        # Extract category
        category_match = re.search(
            r"(?:category|in|type)\s*:?\s*([A-Za-z\s]+?)(?:,|$|\s+in_stock)", text
        )
        if category_match:
            category = category_match.group(1).strip()

        # Extract name - look for the word after product:/item: or between action word and price/category
        # Pattern 1: "product: Mouse" or "item: Keyboard"
        name_match = re.search(r"(?:product|item|name)\s*:\s*([A-Za-z][A-Za-z0-9\s]*?)(?:\s*,|\s+price|\s+for|\s+category|\s+\d)", text)
        
        if not name_match:
            # Pattern 2: Word(s) after add/create/new but before price/category/numbers
            name_match = re.search(r"(?:add|create|new|insert|register)(?:\s+(?:a|an|new))?\s+(?:product|item)?\s*:?\s*([A-Za-z][A-Za-z0-9\s]*?)(?:\s*,|\s+price|\s+for|\s+category|\s+in\s+|\s*\d)", text)
        
        if name_match:
            name = name_match.group(1).strip()
            # Remove common command words that might have been captured
            for word in ["add", "create", "new", "product", "item", "insert", "register"]:
                if name.lower().endswith(word):
                    name = name[:-len(word)].strip()
                if name.lower().startswith(word):
                    name = name[len(word):].strip()

        # Only proceed if we have at least name and price
        if name and price:
            return {
                "name": name,
                "price": price,
                "category": category or "General",
                "in_stock": True,
            }

        return None

    def _match_discount_on_product(self, text: str) -> Optional[dict]:
        """Detect discount on product name like 'calculate 15% discount on keyboard'."""
        if "discount" not in text:
            return None
        
        # Extract discount percentage
        discount_match = re.search(r"(\d+)%?", text)
        if not discount_match:
            return None
        
        # Extract product name (word after 'on' or before discount)
        product_match = re.search(r"(?:on|for)\s+([a-z]+)", text)
        if product_match:
            return {
                "discount": float(discount_match.group(1)),
                "product_name": product_match.group(1)
            }
        return None

    def _match_calculator(self, text: str) -> Optional[dict]:
        """
        Extract calculator operations from text like:
        - 'calculate 15% discount on 100'
        - 'what is 100 times 0.85'
        - 'multiply 100 by 0.85'
        """
        if not any(
            word in text
            for word in ["calculate", "compute", "multiply", "add", "subtract", "divide", "discount"]
        ):
            return None

        # Extract numbers
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        if len(numbers) < 2:
            # Check if it's a discount on product name (handled separately)
            if "discount" in text and re.search(r"\b(on|for)\b", text):
                return None
            return None

        a = float(numbers[0])
        b = float(numbers[1])

        # Determine operation
        if any(word in text for word in ["discount", "off"]):
            # "15% discount" means multiply by 0.85 (1 - 0.15)
            if "%" in text:
                discount_percent = a if a < 100 else b
                price = b if a < 100 else a
                return {
                    "operation": "multiply",
                    "a": price,
                    "b": 1 - (discount_percent / 100),
                }
        elif any(word in text for word in ["multiply", "times", "*", "×"]):
            return {"operation": "multiply", "a": a, "b": b}
        elif any(word in text for word in ["add", "plus", "+"]):
            return {"operation": "add", "a": a, "b": b}
        elif any(word in text for word in ["subtract", "minus", "-"]):
            return {"operation": "subtract", "a": a, "b": b}
        elif any(word in text for word in ["divide", "divided by", "/"]):
            return {"operation": "divide", "a": a, "b": b}

        return None

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"
