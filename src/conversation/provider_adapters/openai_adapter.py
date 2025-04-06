"""
OpenAI history adapter.

Formats conversation history according to OpenAI's API requirements.
"""

from typing import List, Dict, Any, Optional
from .base_adapter import HistoryAdapter

class OpenAIHistoryAdapter(HistoryAdapter):
    """
    History adapter for OpenAI models.
    
    Formats conversation history according to OpenAI's API requirements.
    OpenAI natively supports system, user, assistant, and tool roles.
    """
    
    def format_for_model(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Format conversation history for OpenAI models.
        
        Args:
            messages: The raw conversation history
            tools: Optional list of available tools
            
        Returns:
            Formatted conversation history for OpenAI
        """
        formatted_messages = []
        
        for message in messages:
            role = message["role"]
            
            if role in ["system", "user", "assistant"]:
                # These roles are directly supported by OpenAI
                formatted_msg = {
                    "role": role,
                    "content": message["content"]
                }
                
                # Include tool calls if present for assistant messages
                if role == "assistant" and "tool_calls" in message:
                    formatted_msg["tool_calls"] = message["tool_calls"]
                    
                formatted_messages.append(formatted_msg)
                
            elif role == "tool":
                # Format tool results according to OpenAI's expected format
                formatted_messages.append({
                    "role": "tool",
                    "content": message["content"],
                    "tool_call_id": message.get("tool_call_id", "unknown")
                })
                
        return formatted_messages 