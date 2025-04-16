"""
MCP launcher implementation.

Provides functionality to manage and launch multiple MCP tool servers.
"""

import logging
import os
from typing import Dict, List

from .client_pool import get_client_pool

logger = logging.getLogger(__name__)

class MCPLauncher:
    """
    Manages and launches multiple MCP tool servers.
    
    Provides a unified interface to access all available tools.
    """
    
    def __init__(self):
        """Initialize the MCP launcher."""
        self.client_pool = get_client_pool()
        self.server_paths: Dict[str, str] = {}
        
    def register_server(self, server_name: str, script_path: str) -> None:
        """
        Register an MCP server to be launched.
        
        Args:
            server_name: A unique name for this server
            script_path: Path to the server script
            
        Raises:
            FileNotFoundError: If the server script doesn't exist
        """
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Server script not found: {script_path}")
            
        self.server_paths[server_name] = script_path
        logger.debug(f"Registered server '{server_name}' at {script_path}")
        
    async def launch_all(self) -> None:
        """
        Launch all registered MCP servers and connect clients.
        
        Raises:
            Exception: If any server fails to launch
        """
        logger.debug(f"Launching {len(self.server_paths)} MCP servers...")
        
        try:
            for server_name, script_path in self.server_paths.items():
                await self.client_pool.add_client(server_name, script_path)
                
            logger.debug("All MCP servers launched successfully")
        except Exception as e:
            logger.error(f"Error launching MCP servers: {e}")
            raise
        
    async def shutdown(self) -> None:
        """
        Shutdown all MCP servers and clients.
        
        Raises:
            Exception: If shutdown fails
        """
        try:
            await self.client_pool.cleanup()
            logger.debug("All MCP servers and clients shut down")
        except Exception as e:
            logger.error(f"Error shutting down MCP servers: {e}")
            raise 