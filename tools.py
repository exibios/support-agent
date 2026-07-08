# tools.py

tools = [
    {
        "name": "get_customer",
        "description": (
            "Look up a customer record by name, email address, or customer ID. "
            "Use this tool when you need to verify who you are speaking with or "
            "retrieve account information. Returns the customer's full profile "
            "including account status, contact details, and a list of their order IDs. "
            "Do not use this tool to look up order details — use lookup_order for that." # The phrase "Do not use this tool to look up order details, use lookup_order for that" in get_customer is the most important line in the file. Without this, when a customer gives both their name and an order number in the same message, Claude has to infer which tool handles order lookups. With this line, it knows explicitly. The negative guidance removes the ambiguity that causes misrouting, it's not enough to say what a tool does, you also need to say what it doesn't do when there's a similar tool nearby.
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The search term to find the customer. Can be a full name "
                        "(e.g. 'Sarah Chen'), an email address (e.g. 'sarah@email.com'), "
                        "or a customer ID (e.g. 'CUST-4492')."
                    )
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "lookup_order",
        "description": (
            "Look up a specific order by order ID. Use this tool when you need "
            "details about a particular order — status, items, shipping information, "
            "estimated delivery dates, or notes. Requires a valid order ID. "
            "To find a customer's order IDs, call get_customer first." # reates an explicit dependency between the two tools. Claude now knows that if it needs to look up an order and doesn't have an order ID, the path to getting one is through get_customer. This is the kind of workflow guidance that prevents Claude from trying to pass a customer name into lookup_order and wondering why it doesn't work.
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": (
                        "The order ID to look up. Order IDs follow the format ORD-XXXX "
                        "(e.g. 'ORD-8821'). Must be an exact match."
                    )
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "process_refund",
        "description": (
            "Process a refund to the customer's original payment method. "
            "Requires a verified customer ID and a valid order ID. "
            "Only use this tool after get_customer has successfully confirmed "
            "the customer's identity. Do not call this tool before identity "
            "has been verified — it will fail and you will need to verify first." #The process_refund description explicitly warns that calling it before verification "will fail and you will need to verify first." This isn't just documentation, it's giving Claude the recovery instruction in advance. When the gate fires and returns a permission error, Claude has already been told what to do next. The description and the gate work as a pair.
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": (
                        "The verified customer ID returned by get_customer "
                        "(e.g. 'CUST-4492'). Must match the currently verified customer." # The parameter descriptions include concrete format examples throughout. "e.g. 'Sarah Chen'", "e.g. 'CUST-4492'", "e.g. 'ORD-8821'", these aren't just helpful for humans reading the code. Claude uses them when constructing tool calls, matching input formats against the examples to know what shape the data should take.
                    )
                },
                "order_id": {
                    "type": "string",
                    "description": "The order ID to refund (e.g. 'ORD-8821')."
                },
                "amount": {
                    "type": "number",
                    "description": "The refund amount in USD."
                }
            },
            "required": ["customer_id", "order_id", "amount"]
        }
    }
]