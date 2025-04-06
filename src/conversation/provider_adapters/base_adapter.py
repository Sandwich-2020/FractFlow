"""
Base history adapter.

Defines the interface for provider-specific conversation history adapters.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class HistoryAdapter(ABC):
    """
    Abstract base class for history adapters.
    
    Defines the interface that all history adapters must implement, providing a
    standardized way to format conversation history for different AI providers.
    """
    
    @abstractmethod
    def format_for_model(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Format conversation history for a specific model.
        
        Args:
            messages: The raw conversation history
            tools: Optional list of available tools
            
        Returns:
            Formatted conversation history appropriate for the model
        """
        pass
        
    def format_debug_output(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, label: str = "ADAPTER OUTPUT") -> str:
        """
        Format the adapted message history for debugging purposes.
        
        Args:
            messages: The messages to format
            tools: Optional list of available tools
            label: A label for the debug output
            
        Returns:
            A string representation of the formatted messages
        """
        output = []
        output.append(f"=== {label} DEBUG OUTPUT ===")
        
        # Show tools if available
        if tools:
            output.append(f"Available Tools: {len(tools)}")
            for i, tool in enumerate(tools):
                name = tool.get("function", {}).get("name", "unknown")
                desc = tool.get("function", {}).get("description", "")
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                output.append(f"  Tool {i}: {name} - {desc}")
            output.append("---")

        # Show messages
        for i, message in enumerate(messages):
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