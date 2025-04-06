"""
MCP tool loader implementation.

Provides functionality to load tool schemas from MCP services and
convert them to a standard format for use with the agent system.
"""

from typing import List, Dict, Any
from mcp import ClientSession

class MCPToolLoader:
    """
    Loads tool schemas from MCP services.
    
    Converts MCP tool schemas to a standardized format for use
    with language models.
    """
    
    async def load_tools(self, session: ClientSession) -> List[Dict[str, Any]]:
        """
        Load tool schemas from an MCP client session.
        
        Args:
            session: An initialized MCP ClientSession
            
        Returns:
            List of tool schemas in the standardized format
            
        Raises:
            Exception: If tools can't be loaded
        """
        try:
            # Get available tools from the MCP server
            response = await session.list_tools()
            return self.convert_to_standard_format(response.tools)
        except Exception as e:
            raise ValueError(f"Failed to load tools: {str(e)}")
    
    @staticmethod
    def convert_to_standard_format(tools_data: Any) -> List[Dict[str, Any]]:
        """
        Convert MCP tool schemas to a standardized format.
        
        Args:
            tools_data: MCP tool data
            
        Returns:
            List of tool schemas in the standardized format
        """
        tools = []
        for tool in tools_data:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })
            
        return tools 