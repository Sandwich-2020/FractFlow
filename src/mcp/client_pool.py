"""
MCP client pool implementation.

Provides a client pool for MCP clients, managing the lifecycle of clients
and coordinating tool calls.
"""

import asyncio
import logging
import sys
from typing import Dict, Any, Optional, Tuple
from contextlib import AsyncExitStack

# 检查是否有外部mcp库
try:
    # 尝试显式导入外部MCP库
    import mcp
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
except ImportError:
    # 如果导入失败，给出明确错误消息
    raise ImportError("External MCP library not found. Please install it with 'pip install mcp'.")

logger = logging.getLogger(__name__)

# 单例实例
_instance = None

class MCPClientPool:
    """
    Maintains a pool of MCP clients for different tools.
    
    Provides methods to add clients, call tools, and manage the lifecycle
    of the client connections.
    """
    
    def __init__(self):
        """Initialize the MCP client pool."""
        self.clients: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.tool_to_client: Dict[str, str] = {}  # Maps tool_name to client_name
        
    async def add_client(self, client_name: str, server_script_path: str) -> None:
        """
        Initialize a new MCP client and add it to the pool.
        
        Args:
            client_name: Name to identify this client
            server_script_path: Path to the server script
            
        Raises:
            Exception: If the client cannot be added
        """
        try:
            # Connect to the MCP server using stdio
            server_params = StdioServerParameters(
                command="python",
                args=[server_script_path],
                env=None
            )
            
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
            
            await session.initialize()
            self.clients[client_name] = session
            
            # Map tools to this client
            response = await session.list_tools()
            for tool in response.tools:
                self.tool_to_client[tool.name] = client_name
                
            logger.info(f"Added client '{client_name}' with {len(response.tools)} tools")
            
        except Exception as e:
            logger.error(f"Error adding client '{client_name}': {e}")
            raise
            
    async def call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool using the appropriate client.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            The result from the tool call
            
        Raises:
            Exception: If the tool call fails
        """
        if tool_name not in self.tool_to_client:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        client_name = self.tool_to_client[tool_name]
        client = self.clients[client_name]
        
        try:
            result = await client.call_tool(tool_name, arguments)
            return result.content
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise
            
    async def cleanup(self) -> None:
        """
        Clean up all resources.
        
        Closes all client connections and releases resources.
        """
        try:
            await self.exit_stack.aclose()
            logger.info("All MCP clients cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise

# 移除全局单例变量实例，改用函数获取
def get_client_pool() -> MCPClientPool:
    """
    Get the singleton client pool instance.
    
    Returns:
        The global client pool instance
    """
    global _instance
    if _instance is None:
        _instance = MCPClientPool()
    return _instance 