# tool_runner.py

import json
# Import mock datasets that simulate a database
from mock_data import CUSTOMERS, ORDERS

def process_refund(customer_id: str, order_id: str, amount: float,
                   session_state: dict) -> str:

    # Gate check 1: Has identity verification happened in this session?
    # session_state["verified_customer_id"] starts as None and only gets
    # set when get_customer successfully finds a customer. Using .get()
    # is defensive — if the key is missing entirely (shouldn't happen given
    # our initialisation, but defensive code is good code), it returns None
    # rather than raising a KeyError.
    if not session_state.get("verified_customer_id"):
        return json.dumps({
            "error": {
                "type": "permission",
                "retryable": False,
                "message": (
                    "Cannot process a refund before customer identity has been "
                    "verified. Call get_customer first and confirm the customer's "
                    "identity before attempting a refund."
                )
            }
        })

    # Gate check 2: Does the customer_id in this refund request match
    # the customer who was actually verified in this session?
    # This closes a real security gap: if Claude has seen multiple customer
    # records in a conversation (from retries, corrections, or edge cases),
    # it might pass the wrong customer_id to this function. This check
    # ensures the refund always targets the specifically verified customer,
    # regardless of what else Claude has seen in the conversation.
    if customer_id != session_state["verified_customer_id"]:
        return json.dumps({
            "error": {
                "type": "permission",
                "retryable": False,
                "message": (
                    f"Customer ID mismatch. The verified customer in this session is "
                    f"{session_state['verified_customer_id']} but the refund request "
                    f"is for {customer_id}. Do not process this refund. Verify you "
                    f"have the correct customer before continuing."
                )
            }
        })

    # Both gates passed. Now do the actual work.
    # The principle: validate everything before doing anything irreversible.

    # Check the order exists before attempting the refund
    if order_id not in ORDERS:
        return json.dumps({
            "error": {
                "type": "validation",
                "retryable": False,
                "message": (
                    f"Order {order_id} not found. Verify the order ID with the "
                    "customer and try again."
                )
            }
        })

    # Check the order belongs to the verified customer.
    # A verified customer shouldn't be able to trigger a refund on someone
    # else's order just by knowing the order ID. This cross-reference
    # catches that case before any money moves.
    order = ORDERS[order_id]
    if order["customer_id"] != session_state["verified_customer_id"]:
        return json.dumps({
            "error": {
                "type": "permission",
                "retryable": False,
                "message": (
                    f"Order {order_id} does not belong to the verified customer. "
                    "Do not process this refund."
                )
            }
        })

    # All checks passed — process the refund.
    # In production this would call a payments API. Here we return a
    # simulated successful response with the fields a real API would return.
    return json.dumps({
        "success": True,
        "refund_id": "REF-" + order_id.split("-")[1],
        "customer_id": customer_id,
        "order_id": order_id,
        "amount": amount,
        "status": "initiated",
        "message": (
            f"Refund of ${amount:.2f} for order {order_id} has been initiated. "
            "Funds will return to the original payment method within 3-5 business days."
        )
    })

# Fetch a customer by matching against multiple possible identifiers
def get_customer(query: str,session_state:dict) -> str:
    # Normalize input for consistent matching (ignore case + extra spaces)
    query = query.strip().lower()

    # Iterate through all customers in the dataset
    for customer in CUSTOMERS.values():
        # Match against customer_id, email, or name
        # This makes the tool flexible in how it can be called
        if (
            query == customer["customer_id"].lower()
            or query == customer["email"].lower()
            or query == customer["name"].lower()
        ):
             # Verification successful — write to session state before returning.
            # This write is what unlocks the process_refund gate later in
            # the conversation. The ordering matters: we write after confirming
            # the customer exists but before returning, so state always reflects
            # what actually happened rather than what was attempted.

            # Write verified identity into session state before returning.
            # This is what downstream gates check — if these values are set,
            # it means this function ran successfully and found a real customer.
            session_state["verified_customer_id"] = customer["customer_id"]
            session_state["verified_customer_name"] = customer["name"]

            # Return the matched customer as a JSON string
            return json.dumps(customer)
        
    # No match found — return a structured validation error.
    # retryable: False because sending the same query again won't help.
    # The message tells Claude both what went wrong and what alternatives
    # are available (name, email, or ID), giving it a clear recovery path.

    # If no match is found, return a structured error response
    return json.dumps({
        "error": {
            "type": "validation",
            "retryable": False,
            "message": (
                f"No customer found matching '{query}'. The input may be "
                "misspelled or in the wrong format. Customer IDs follow the "
                "format CUST-XXXX. You can also search by full name or email "
                "address. Ask the customer to verify their details and try again."
            )
        }
    })


# Fetch an order using its order ID
def lookup_order(order_id: str,session_state: dict) -> str:
    # Normalize input (strip spaces + standardize casing)
    # Customers sometimes type order IDs in lowercase — strip and uppercase
    # before checking so 'ord-8821' finds the same record as 'ORD-8821'.
    order_id = order_id.strip().upper()

    # Check if the order exists in the dataset
    if order_id in ORDERS:
        # Return the order details as a JSON string
        return json.dumps(ORDERS[order_id])

    # Return a structured error if the order is not found
    return json.dumps({
        "error": {
            "type": "validation",
            "retryable": False,
            "message": (
                f"No order found with ID '{order_id}'. "
                "Please check the order ID and try again."
            )
        }
    })


# Central dispatcher that routes tool calls to the correct function
def run_tool(tool_name: str, tool_input: dict,session_state: dict) -> str:
    # run_tool is the single routing point for all tool execution.
    # Every tool call from Claude goes through here, which means session_state
    # only needs to be threaded through one place rather than multiple call sites.
    # Any new tool you add gets access to session state automatically just by
    # being added to this routing function.
    # Route to the appropriate tool based on its name
    if tool_name == "get_customer":
        # Expecting "query" in tool_input
        return get_customer(tool_input["query"],session_state)

    elif tool_name == "lookup_order":
        # Expecting "order_id" in tool_input
        return lookup_order(tool_input["order_id"],session_state)

    elif tool_name == "process_refund":
        return process_refund(
            tool_input["customer_id"]
            ,tool_input["order_id"]
            ,tool_input["amount"]
            ,session_state
        )
    else:
        # Handle unknown tool calls safely with a structured error
        return json.dumps({
            "error": {
                "type": "validation",
                "retryable": False,
                "message": f"Tool '{tool_name}' is not recognised."
            }
        })