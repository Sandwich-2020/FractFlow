"""
Base conversation history management.

Provides a central class for managing conversation history with support for
different message types and provider-specific adapters.
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

class BaseConversationHistory(ABC):
    """
    Abstract base class for conversation history management.
    
    Defines the interface that all conversation history implementations must implement,
    providing a standardized way to manage conversation history.
    """
    
    @abstractmethod
    def add_system_message(self, content: str) -> None:
        """
        Add a system message to the conversation history.
        
        Args:
            content: The system message content
        """
        pass
    
    @abstractmethod
    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the conversation history.
        
        Args:
            content: The user message content
        """
        pass
    
    @abstractmethod
    def add_assistant_message(self, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Add an assistant message to the conversation history.
        
        Args:
            content: The assistant message content
            tool_calls: Optional list of tool calls made by the assistant
        """
        pass
    
    @abstractmethod
    def add_tool_result(self, tool_name: str, result: str, tool_call_id: Optional[str] = None) -> None:
        """
        Add a tool result to the conversation history.
        
        Args:
            tool_name: Name of the tool
            result: Result from the tool
            tool_call_id: Optional ID of the tool call this is responding to
        """
        pass
    
    @abstractmethod
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get the full message history.
        
        Returns:
            The list of all messages in the conversation
        """
        pass
    
    @abstractmethod
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """
        Get the last message in the conversation.
        
        Returns:
            The last message or None if history is empty
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the conversation history, except for any system messages."""
        pass
    
    @abstractmethod
    def format_debug_output(self) -> str:
        """
        Format the message history for debugging purposes.
        
        Returns:
            A string representation of the entire conversation history
        """
        pass


class ConversationHistory(BaseConversationHistory):
    """
    Default implementation of conversation history management.
    
    Maintains an internal representation of messages and provides
    methods to add different types of messages and retrieve
    formatted history.
    """
    
    def __init__(self, system_prompt: str = ""):
        """
        Initialize the conversation history.
        
        Args:
            system_prompt: Initial system prompt to set
        """
        self.messages = []
        if system_prompt:
            self.add_system_message(system_prompt)
    
    def add_system_message(self, content: str) -> None:
        """
        Add a system message to the conversation history.
        
        Args:
            content: The system message content
        """
        self.messages.append({
            "role": "system",
            "content": content
        })
    
    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the conversation history.
        
        Args:
            content: The user message content
        """
        self.messages.append({
            "role": "user", 
            "content": content
        })
    
    def add_assistant_message(self, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Add an assistant message to the conversation history.
        
        Args:
            content: The assistant message content
            tool_calls: Optional list of tool calls made by the assistant
        """
        message = {
            "role": "assistant",
            "content": content
        }
        
        if tool_calls:
            message["tool_calls"] = tool_calls
            
        self.messages.append(message)
    
    def add_tool_result(self, tool_name: str, result: str, tool_call_id: Optional[str] = None) -> None:
        """
        Add a tool result to the conversation history.
        
        Args:
            tool_name: Name of the tool
            result: Result from the tool
            tool_call_id: Optional ID of the tool call this is responding to
        """
        message = {
            "role": "tool",
            "tool_name": tool_name,
            "content": result
        }
        
        if tool_call_id:
            message["tool_call_id"] = tool_call_id
            
        self.messages.append(message)
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get the full message history.
        
        Returns:
            The list of all messages in the conversation
        """
        return self.messages
    
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """
        Get the last message in the conversation.
        
        Returns:
            The last message or None if history is empty
        """
        return self.messages[-1] if self.messages else None
    
    def clear(self) -> None:
        """Clear the conversation history, except for any system messages."""
        system_messages = [msg for msg in self.messages if msg["role"] == "system"]
        self.messages = system_messages
        
    def format_debug_output(self) -> str:
        """
        Format the message history for debugging purposes.
        
        Returns:
            A string representation of the entire conversation history
        """
        output = []
        output.append("=== CONVERSATION HISTORY DEBUG OUTPUT ===")
        
        for i, message in enumerate(self.messages):
            role = message.get("role", "unknown")
            content_preview = message.get("content", "")
            if len(content_preview) > 50:
                content_preview = content_preview[:47] + "..."
                
            # Format based on message type
            if role == "system":
                output.append(f"[{i}] SYSTEM: {content_preview}")
            elif role == "user":
                output.append(f"[{i}] USER: {content_preview}")
            elif role == "assistant":
                tool_calls = ""
                if "tool_calls" in message:
                    tool_names = [tc.get("name", "unknown") for tc in message.get("tool_calls", [])]
                    tool_calls = f" [TOOLS: {', '.join(tool_names)}]"
                output.append(f"[{i}] ASSISTANT{tool_calls}: {content_preview}")
            elif role == "tool":
                tool_name = message.get("tool_name", "unknown")
                output.append(f"[{i}] TOOL [{tool_name}]: {content_preview}")
            else:
                output.append(f"[{i}] UNKNOWN: {content_preview}")
                
        output.append("========================================")
        return "\n".join(output) 