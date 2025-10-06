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
    from workflow import llm, logger

    messages = state["messages"]
    attempt_count = state.get("attempt_count", 0)

    # Invoke LLM to reason about next step
    try:
        response = llm.invoke(messages)

        # Extract reasoning and payload from response
        # The LLM should structure its response with reasoning before calling the tool

        logger.log_attempt(
            attempt_num=attempt_count + 1,
            reasoning=response.content,
            payload=extract_payload_from_response(response)
        )

        return {
            "messages": messages + [response],
            "attempt_count": attempt_count + 1
        }
    except Exception as e:
        logger.log_error(f"Error in reasoning node: {str(e)}")
        return {
            "messages": messages,
            "attempt_count": attempt_count,
            "error": str(e)
        }


def tool_execution_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool execution node - calls the MCP tool with the LLM's chosen payload.
    """
    from workflow import mcp_client, logger

    messages = state["messages"]
    last_message = messages[-1]

    # Extract tool calls from the last message
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        # No tool call, skip
        return {"messages": messages}

    tool_results = []

    for tool_call in last_message.tool_calls:
        try:
            # Execute the tool via MCP client
            result = mcp_client.call_tool(
                name=tool_call["name"],
                arguments=tool_call["args"]
            )

            # Log the result
            logger.log_result(result)

            # Create tool message with result
            tool_message = ToolMessage(
                content=json.dumps(result),
                tool_call_id=tool_call["id"]
            )
            tool_results.append(tool_message)

        except Exception as e:
            logger.log_error(f"Error executing tool: {str(e)}")
            tool_message = ToolMessage(
                content=json.dumps({"error": str(e)}),
                tool_call_id=tool_call["id"]
            )
            tool_results.append(tool_message)

    return {
        "messages": messages + tool_results
    }


def success_detection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks if the last tool execution successfully retrieved /etc/passwd.
    """
    from workflow import logger

    messages = state["messages"]

    # Check last message for success pattern
    if messages and isinstance(messages[-1], ToolMessage):
        content = messages[-1].content

        if re.search(SUCCESS_PATTERN, content):
            # Success! We found /etc/passwd content
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
        "continue" - Try another attack
        "success" - Successfully escaped
        "max_attempts" - Reached maximum attempts
    """
    from config import MAX_ATTEMPTS

    # Check if successful
    if state.get("success"):
        return "success"

    # Check if max attempts reached
    if state.get("attempt_count", 0) >= MAX_ATTEMPTS:
        return "max_attempts"

    # Check for errors
    if state.get("error"):
        return "error"

    # Continue attacking
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
