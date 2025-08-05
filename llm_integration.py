import os
from dotenv import load_dotenv
from openai import OpenAI
import json # Ensure json is imported

# Load environment variables
load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

def get_llm_response(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
    """
    Sends a prompt to the OpenAI LLM and returns the response.
    Best for general conversational responses.

    Args:
        prompt (str): The prompt to send to the LLM.
        model (str): The OpenAI model to use (e.g.,"gpt-4o").
        temperature (float): Controls the randomness of the output.

    Returns:
        str: The LLM's response.
    """
    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error getting LLM response: {e}")
        return "An error occurred while getting LLM response."

def get_llm_tool_response(
    messages: list,
    tools: list,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.0, # Often 0.0 for tool calling to ensure deterministic output
    tool_choice: str = "auto" # Force specific tool, or 'auto' for LLM to decide
) -> dict:
    """
    Sends messages to the OpenAI LLM with tool definitions and returns the response,
    which could be a tool call or a text response.

    Args:
        messages (list): A list of message dictionaries (e.g., [{"role": "user", "content": "..."}]).
        tools (list): A list of tool definitions (JSON schema).
        model (str): The OpenAI model to use.
        temperature (float): Controls randomness.
        tool_choice (str): "auto" or {"type": "function", "function": {"name": "tool_name"}}.

    Returns:
        dict: The LLM's raw response, potentially containing tool calls.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
        )
        return response.choices[0].message
    except Exception as e:
        print(f"Error getting LLM tool response: {e}")
        return {"role": "assistant", "content": f"An error occurred: {e}"}

# def test_llm_integration():
#     """
#     Tests the LLM integration with a simple prompt and a tool-calling example.
#     """
#     print("--- Testing LLM Integration ---")
#     test_prompt_text = "What is the capital of France?"
#     print(f"Sending prompt (text-only): '{test_prompt_text}'")
#     response_text = get_llm_response(test_prompt_text)
#     print(f"LLM Response (text-only): {response_text}")

#     print("\n--- Testing LLM Tool Calling ---")
#     # Example tool definition (a dummy one for testing)
#     example_tools = [
#         {
#             "type": "function",
#             "function": {
#                 "name": "get_current_weather",
#                 "description": "Get the current weather in a given location",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "location": {
#                             "type": "string",
#                             "description": "The city and state, e.g. San Francisco, CA",
#                         },
#                         "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
#                     },
#                     "required": ["location"],
#                 },
#             },
#         }
#     ]
#     test_messages = [{"role": "user", "content": "What's the weather like in London?"}]
#     print(f"Sending prompt (tool-calling): '{test_messages[0]['content']}' with dummy tool.")
#     response_tool_call = get_llm_tool_response(messages=test_messages, tools=example_tools)
#     print(f"LLM Response (tool-calling): {response_tool_call}")
#     if response_tool_call.tool_calls:
#         print(f"LLM suggested tool call: {response_tool_call.tool_calls[0].function.name} with args: {json.loads(response_tool_call.tool_calls[0].function.arguments)}")
#     else:
#         print("LLM did not suggest a tool call.")
#     print("--- LLM Integration Test Complete ---")


# if __name__ == "__main__":
#     test_llm_integration()