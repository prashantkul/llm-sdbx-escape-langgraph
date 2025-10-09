"""
LangGraph nodes for the security researcher agent workflow.
"""

import re
import json
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from config import SUCCESS_PATTERN


def reasoning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM reasoning node - analyzes current state and decides next action.

    This node is where the LLM plans the next injection attempt based on
    previous results and error messages.
    """
    import sys

    # Get llm and logger from __main__ module
    main_module = sys.modules['__main__']
    llm = main_module.llm
    logger = main_module.logger
    messages = state["messages"]
    attempt_count = state.get("attempt_count", 0)

    # Invoke LLM to reason about next step
    try:
        response = llm.invoke(messages)

        # Debug: Print what the LLM returned
        has_tool_calls = hasattr(response, 'tool_calls') and response.tool_calls
        print(f"[DEBUG] LLM response - has_tool_calls: {has_tool_calls}, content_len: {len(response.content) if response.content else 0}")
        if has_tool_calls:
            print(f"[DEBUG] Tool calls: {response.tool_calls}")

        # Log the attempt
        if logger:
            logger.log_attempt(
                attempt_num=attempt_count + 1,
                reasoning=response.content,
                payload=""  # Will be extracted from tool calls later
            )

        return {
            "messages": [response],
            "attempt_count": attempt_count + 1
        }
    except Exception as e:
        if logger:
            logger.log_error(f"Error in reasoning node: {str(e)}")
        return {
            "attempt_count": attempt_count,
            "error": str(e)
        }


async def _invoke_tool_async(tool, args):
    """Helper to invoke tool asynchronously."""
    return await tool.ainvoke(args)

def tool_execution_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool execution node - calls the MCP tools with the LLM's chosen payload.
    """
    import sys
    import asyncio
    import threading
    from langchain_core.messages import ToolMessage

    # Get mcp_tools and logger from __main__ module
    main_module = sys.modules['__main__']
    mcp_tools = main_module.mcp_tools
    logger = main_module.logger
    messages = state["messages"]
    last_message = messages[-1]
    mode = state.get("mode", "interactive")

    # Extract tool calls from the last message
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        # No tool call - in interactive mode, this means we're done
        if mode == "interactive":
            return {"success": True}  # Mark as complete so we exit
        return {}

    tool_results = []

    for tool_call in last_message.tool_calls:
        print(f"[DEBUG] Processing tool call: {tool_call}")
        try:
            # Find the matching tool
            tool_name = tool_call["name"]
            tool = next((t for t in mcp_tools if t.name == tool_name), None)

            if not tool:
                print(f"[DEBUG] Tool '{tool_name}' not found")
                tool_message = ToolMessage(
                    content=f"Error: Tool '{tool_name}' not found",
                    tool_call_id=tool_call["id"]
                )
                tool_results.append(tool_message)
                continue

            # Execute the tool - handle event loop properly
            print(f"[DEBUG] Invoking tool '{tool_name}' with args: {tool_call['args']}")

            # Check if we're in an event loop
            try:
                loop = asyncio.get_running_loop()
                # If in event loop, use threading
                result_holder = []
                exception_holder = []

                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result = new_loop.run_until_complete(_invoke_tool_async(tool, tool_call["args"]))
                        result_holder.append(result)
                        new_loop.close()
                    except Exception as e:
                        exception_holder.append(e)

                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()

                if exception_holder:
                    raise exception_holder[0]
                result = result_holder[0]
            except RuntimeError:
                # No event loop, safe to use asyncio.run()
                result = asyncio.run(_invoke_tool_async(tool, tool_call["args"]))

            print(f"[DEBUG] Tool result: {result}")

            # Log the result
            if logger:
                logger.log_result({"tool": tool_name, "args": tool_call["args"], "result": str(result)[:500]})

            # Create tool message with result
            tool_message = ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
            tool_results.append(tool_message)

        except Exception as e:
            print(f"[DEBUG] Tool execution error: {e}")
            import traceback
            traceback.print_exc()
            if logger:
                logger.log_error(f"Error executing tool: {str(e)}")
            tool_message = ToolMessage(
                content=f"Error: {str(e)}",
                tool_call_id=tool_call["id"]
            )
            tool_results.append(tool_message)

    return {
        "messages": tool_results
    }


def success_detection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks if the last tool execution successfully retrieved /etc/passwd.
    """
    import sys
    from langchain_core.messages import ToolMessage

    # Get logger from __main__ module
    main_module = sys.modules['__main__']
    logger = main_module.logger
    messages = state["messages"]

    # Check last message for success pattern
    if messages and isinstance(messages[-1], ToolMessage):
        content = messages[-1].content

        if re.search(SUCCESS_PATTERN, content):
            # Success! We found /etc/passwd content
            if logger:
                logger.log_success(
                    attempt_num=state["attempt_count"],
                    payload=extract_last_payload(messages),
                    output=content
                )
            return {
                "success": True,
                "target_content": content
            }

    return {"success": False}


def should_continue(state: Dict[str, Any]) -> str:
    """
    Conditional edge function - decides whether to continue attacking or stop.

    Returns:
        "continue" - Try another attack (auto mode) or completed response (interactive mode)
        "success" - Successfully escaped (auto mode only)
        "max_attempts" - Reached maximum attempts (auto mode only)
        "error" - Error occurred
    """
    from config import MAX_ATTEMPTS

    attempt_count = state.get("attempt_count", 0)
    mode = state.get("mode", "interactive")
    print(f"[DEBUG] should_continue: mode={mode}, attempt_count={attempt_count}, success={state.get('success')}, error={state.get('error')}")

    # Check for errors first (applies to both modes)
    if state.get("error"):
        return "error"

    # Interactive mode: Always end after one response cycle
    if mode == "interactive":
        # End the conversation after agent responds
        return "success"  # Use "success" to end the graph

    # Auto mode: Check for success and attempt limits
    if state.get("success"):
        return "success"

    if attempt_count >= MAX_ATTEMPTS:
        return "max_attempts"

    # Continue attacking in auto mode
    return "continue"


def extract_payload_from_response(response: AIMessage) -> str:
    """Extract the command payload from LLM response."""
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call.get("name") == "execute_shell_command":
                return tool_call.get("args", {}).get("command", "")
    return ""


def extract_last_payload(messages: List) -> str:
    """Extract the last payload from message history."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls'):
            for tool_call in msg.tool_calls:
                if tool_call.get("name") == "execute_shell_command":
                    return tool_call.get("args", {}).get("command", "")
    return ""
