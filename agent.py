# agent.py

# Load environment variables (e.g., API keys from .env file)
from dotenv import load_dotenv
# Official Anthropic client for interacting with Claude models
from anthropic import Anthropic
# Tool definitions (what Claude is allowed to use)
from tools import tools
# Local execution layer for actually running tools
from tool_runner import run_tool
import json
import logging
import os
# Load environment variables into the runtime
load_dotenv()

# Initialize Anthropic client
# client = Anthropic() # Anthopic
client = Anthropic(
  api_key=os.getenv("ANTHROPIC_API_KEY", ""),
  base_url="https://openrouter.ai/api",
)

# System prompt defines the agent's behavior, constraints, and workflow
SYSTEM_PROMPT = """You are a customer support agent for an online retailer.
You have access to tools that let you look up customer records, order details,
and process refunds.

When a customer contacts you:
1. Always look up their account using get_customer before doing anything else.
2. Use lookup_order to get details on any specific order they mention.
3. Only process refunds after you have verified the customer's identity
   with get_customer. The system will block refunds attempted before verification.
4. Give clear, helpful responses based on what you find.
5. If you cannot find a customer or order, tell them politely and ask them
   to double-check the information they provided.

Always verify who you are speaking with before discussing account details
or processing any financial transactions."""


# Core agent loop: takes a user message and returns a final response
def run_agent(user_message: str) -> str:
    # Initialize conversation history with the user's first message
    conversation_history = [
        {"role": "user", "content": user_message}
    ]
    
    # Session state tracks verified identity and any other conditions
    # that need to persist across tool calls within this conversation.
    # It starts empty at the beginning of every conversation — there is
    # no carry-over between sessions, which is intentional. Each customer
    # interaction starts fresh with no inherited state from previous ones.
    session_state = {
        "verified_customer_id": None,
        "verified_customer_name": None
    }

    # Loop until Claude finishes the interaction
    try:
        while True:
            # Send current state (history + tools + system prompt) to Claude
            response = client.messages.create(
                model="openrouter/free",
                #model="anthropic/claude-sonnet-4-6",
                #model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=conversation_history

            )

            # Always append Claude's response immediately
            # This preserves the full chain: assistant → tool call → tool result → next turn

            # Append Claude's response before checking stop_reason.
            # This ensures the assistant message always ends up in history,
            # including the final end_turn response. If you appended after
            # the stop_reason check instead, the last message would be missing
            # from the conversation history on end_turn.
            conversation_history.append({
                "role": "assistant",
                "content": response.content
            })

            # If Claude has finished responding (no more tool calls needed)
            if response.stop_reason == "end_turn":
                # Extract and return the text response from content blocks
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text
                # Fallback in case no text block is found
                return ""

            # If Claude wants to use tools
            if response.stop_reason == "tool_use":
                tool_results = []

                # Iterate through all tool_use blocks (Claude may call multiple tools at once)
                for block in response.content:
                    if block.type == "tool_use":
                        # Execute the tool locally with provided inputs, # session_state gets passed through every tool call

                        # Pass session_state into every tool call through run_tool.
                        # Tools that need it (like process_refund) will read from it.
                        # Tools that don't (like lookup_order currently) still receive
                        # it for consistency — adding state awareness to a tool later
                        # won't require changing this call site.

                        result = run_tool(block.name, block.input,session_state)

                        # Collect tool results in the required format
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,  # Links result to specific tool call
                            "content": result
                        })

                # Send all tool results back in a single user message
                # This allows Claude to continue reasoning with fresh data
                conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
    except Exception:
        # Catch-all: anything unexpected here (API failure, malformed response,
        # a tool raising instead of returning a JSON error, etc.) would otherwise
        # propagate and kill the whole CLI session over a single bad turn.
        # Log with session_state since it's the one piece of state that explains
        # what the conversation had established by the time it died.
        logging.exception(
            "Unhandled error in run_agent (turns_so_far=%d, session_state=%s)",
            len(conversation_history), session_state
        )
        return json.dumps({
            "error": {
                "type": "internal",
                "retryable": False,
                "message": "Something went wrong while processing your request. Please try again."
            }
        })


# Entry point for running the agent in a CLI loop
if __name__ == "__main__":
    print("Customer Support Agent, Stage 2")
    print("Type 'quit' to exit")
    print("=" * 40)

    while True:
        # Read user input from terminal
        user_input = input("\nCustomer: ").strip()

        # Ignore empty input
        if not user_input:
            continue

        # Exit conditions
        if user_input.lower() in ("quit", "exit", "q"):
            break

        # Print agent response (stream-like UX with flush)
        print("\nAgent:", end=" ", flush=True)
        response = run_agent(user_input)
        print(response)