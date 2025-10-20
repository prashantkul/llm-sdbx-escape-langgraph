"""
Victim Agent Interface

Communicates with the LangGraph agent (Gemini) via LangGraph SDK.
"""

from langgraph_sdk import get_client
import asyncio
from typing import Dict, Any, Optional
import logging

from config import Config


class VictimAgent:
    """Interface to the victim LangGraph agent."""

    def __init__(self, langgraph_url: str = None, assistant_id: str = "security-researcher"):
        """
        Initialize victim agent interface.

        Args:
            langgraph_url: URL of LangGraph server
            assistant_id: ID of the assistant to use
        """
        self.langgraph_url = langgraph_url or Config.LANGGRAPH_URL
        self.assistant_id = assistant_id

        # Get LangGraph SDK client
        self.client = get_client(url=self.langgraph_url)

        # Create event loop
        try:
            self.loop = asyncio.get_event_loop()
            if self.loop.is_closed():
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        self.logger = logging.getLogger(__name__)

    async def send_message_async(self, message: str) -> Dict[str, Any]:
        """
        Send message to victim agent asynchronously.

        Args:
            message: The attack prompt to send

        Returns:
            Agent's response
        """
        try:
            # Create a new thread
            thread = await self.client.threads.create()

            # Send message and wait for completion
            response = await self.client.runs.wait(
                thread["thread_id"],
                self.assistant_id,
                input={"messages": [{"role": "user", "content": message}]}
            )

            return response

        except Exception as e:
            self.logger.error(f"Failed to communicate with victim agent: {e}")
            return {
                "error": str(e),
                "response": ""
            }

    def send_message(self, message: str) -> Dict[str, Any]:
        """
        Send message to victim agent (synchronous wrapper).

        Args:
            message: The attack prompt to send

        Returns:
            Agent's response
        """
        return self.loop.run_until_complete(self.send_message_async(message))

    def extract_response_text(self, response: Dict[str, Any]) -> str:
        """
        Extract readable text from agent response.

        Args:
            response: Raw response from agent

        Returns:
            Extracted text
        """
        if "error" in response:
            return f"Error: {response['error']}"

        # Extract messages from LangGraph response
        try:
            if "values" in response and "messages" in response["values"]:
                messages = response["values"]["messages"]
                if messages and len(messages) > 0:
                    # Get the last AI message
                    for msg in reversed(messages):
                        if hasattr(msg, 'content'):
                            return msg.content
                        elif isinstance(msg, dict) and 'content' in msg:
                            return msg['content']

            # Fallback: return full response as string
            return str(response)

        except Exception as e:
            self.logger.error(f"Error extracting response text: {e}")
            return str(response)

    def check_agent_health(self) -> bool:
        """
        Check if victim agent is responsive.

        Returns:
            True if agent is healthy
        """
        try:
            # Try to create a thread as a health check
            loop = asyncio.new_event_loop()
            thread = loop.run_until_complete(self.client.threads.create())
            loop.close()
            return thread is not None
        except:
            return False

    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'loop') and not self.loop.is_closed():
            self.loop.close()
