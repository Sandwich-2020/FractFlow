import pytest
import unittest.mock as mock
import asyncio
from src.core.orchestrator import Orchestrator
from src.core.query_processor import QueryProcessor
from src.core.tool_executor import ToolExecutor
from src.models.base_model import BaseModel

class TestAgentIntegration:
    """测试代理集成"""
    
    @mock.patch('src.core.orchestrator.create_model')
    @mock.patch('src.mcp.launcher.MCPLauncher')
    @mock.patch('src.mcp.tool_loader.MCPToolLoader')
    async def test_process_query_without_tools(self, mock_tool_loader_class, mock_launcher_class, mock_create_model):
        """测试处理没有工具调用的查询"""
        # 设置模拟模型
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        
        # 设置模拟工具
        mock_tools = []
        mock_tool_loader = mock.MagicMock()
        mock_tool_loader_class.return_value = mock_tool_loader
        
        # 设置load_tools返回协程
        tools_future = asyncio.Future()
        tools_future.set_result(mock_tools)
        mock_tool_loader.load_tools.return_value = tools_future
        
        # 设置模拟会话
        mock_session = mock.MagicMock()
        mock_launcher = mock.MagicMock()
        mock_launcher_class.return_value = mock_launcher
        
        # 使launch_all返回协程
        launch_future = asyncio.Future()
        launch_future.set_result(None)
        mock_launcher.launch_all.return_value = launch_future
        
        # 设置shutdown返回协程
        shutdown_future = asyncio.Future()
        shutdown_future.set_result(None)
        mock_launcher.shutdown.return_value = shutdown_future
        
        # 设置client_pool
        mock_launcher.client_pool.clients = {"test_client": mock_session}
        
        # 设置模型执行结果 - 没有工具调用
        mock_model.execute.return_value = {
            "choices": [{
                "message": {
                    "content": "This is a response without tool calls.",
                    "tool_calls": None
                }
            }]
        }
        
        # 创建组件
        orchestrator = Orchestrator()
        tool_executor = ToolExecutor()
        query_processor = QueryProcessor(orchestrator, tool_executor)
        
        # 启动协调器
        await orchestrator.start()
        
        try:
            # 处理查询
            result = await query_processor.process_query("What is the meaning of life?")
            
            # 验证结果
            assert result == "This is a response without tool calls."
            
            # 验证调用
            mock_model.add_user_message.assert_called_once_with("What is the meaning of life?")
            mock_model.execute.assert_called_once()
            mock_model.add_assistant_message.assert_not_called()
            mock_model.add_tool_result.assert_not_called()
        finally:
            await orchestrator.shutdown()
    
    @mock.patch('src.core.orchestrator.create_model')
    @mock.patch('src.mcp.launcher.MCPLauncher')
    @mock.patch('src.mcp.tool_loader.MCPToolLoader')
    async def test_process_query_with_tool_call(self, mock_tool_loader_class, mock_launcher_class, mock_create_model):
        """测试处理带有工具调用的查询"""
        # 设置模拟模型
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        
        # 设置模拟工具
        mock_tools = [{"type": "function", "function": {"name": "weather"}}]
        mock_tool_loader = mock.MagicMock()
        mock_tool_loader_class.return_value = mock_tool_loader
        
        # 设置load_tools返回协程
        tools_future = asyncio.Future()
        tools_future.set_result(mock_tools)
        mock_tool_loader.load_tools.return_value = tools_future
        
        # 设置模拟会话
        mock_session = mock.MagicMock()
        mock_launcher = mock.MagicMock()
        mock_launcher_class.return_value = mock_launcher
        
        # 使launch_all返回协程
        launch_future = asyncio.Future()
        launch_future.set_result(None)
        mock_launcher.launch_all.return_value = launch_future
        
        # 设置shutdown返回协程
        shutdown_future = asyncio.Future()
        shutdown_future.set_result(None)
        mock_launcher.shutdown.return_value = shutdown_future
        
        # 设置client_pool
        mock_launcher.client_pool.clients = {"test_client": mock_session}
        
        # 设置两轮模型执行结果
        # 第一轮：调用工具
        # 第二轮：返回最终回答
        mock_model.execute.side_effect = [
            {
                "choices": [{
                    "message": {
                        "content": "Let me check the weather for you.",
                        "tool_calls": [
                            {"name": "weather", "id": "call_123", "arguments": {"location": "New York"}}
                        ]
                    }
                }]
            },
            {
                "choices": [{
                    "message": {
                        "content": "The weather in New York is sunny, 25°C.",
                        "tool_calls": None
                    }
                }]
            }
        ]
        
        # 设置模拟工具执行器
        mock_tool_result = "Sunny, 25°C"
        mock_tool_executor = mock.MagicMock(spec=ToolExecutor)
        
        # 使execute_tool返回协程
        tool_result_future = asyncio.Future()
        tool_result_future.set_result(mock_tool_result)
        mock_tool_executor.execute_tool.return_value = tool_result_future
        
        # 创建组件
        orchestrator = Orchestrator()
        query_processor = QueryProcessor(orchestrator, mock_tool_executor)
        
        # 启动协调器
        await orchestrator.start()
        
        try:
            # 处理查询
            result = await query_processor.process_query("What's the weather in New York?")
            
            # 验证结果
            assert result == "The weather in New York is sunny, 25°C."
            
            # 验证调用
            mock_model.add_user_message.assert_called_once_with("What's the weather in New York?")
            assert mock_model.execute.call_count == 2
            mock_model.add_assistant_message.assert_called_once()
            mock_tool_executor.execute_tool.assert_called_once_with(
                "weather", {"location": "New York"}
            )
            mock_model.add_tool_result.assert_called_once_with(
                "weather", mock.ANY, "call_123"
            )
        finally:
            await orchestrator.shutdown()
    
    @mock.patch('src.core.orchestrator.create_model')
    @mock.patch('src.mcp.launcher.MCPLauncher')
    @mock.patch('src.mcp.tool_loader.MCPToolLoader')
    async def test_process_query_with_tool_error(self, mock_tool_loader_class, mock_launcher_class, mock_create_model):
        """测试处理工具执行错误"""
        # 设置模拟模型
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        
        # 设置模拟工具
        mock_tools = [{"type": "function", "function": {"name": "weather"}}]
        mock_tool_loader = mock.MagicMock()
        mock_tool_loader_class.return_value = mock_tool_loader
        
        # 设置load_tools返回协程
        tools_future = asyncio.Future()
        tools_future.set_result(mock_tools)
        mock_tool_loader.load_tools.return_value = tools_future
        
        # 设置模拟会话
        mock_session = mock.MagicMock()
        mock_launcher = mock.MagicMock()
        mock_launcher_class.return_value = mock_launcher
        
        # 使launch_all返回协程
        launch_future = asyncio.Future()
        launch_future.set_result(None)
        mock_launcher.launch_all.return_value = launch_future
        
        # 设置shutdown返回协程
        shutdown_future = asyncio.Future()
        shutdown_future.set_result(None)
        mock_launcher.shutdown.return_value = shutdown_future
        
        # 设置client_pool
        mock_launcher.client_pool.clients = {"test_client": mock_session}
        
        # 设置模型执行结果
        mock_model.execute.side_effect = [
            {
                "choices": [{
                    "message": {
                        "content": "Let me check the weather for you.",
                        "tool_calls": [
                            {"name": "weather", "id": "call_123", "arguments": {"location": "New York"}}
                        ]
                    }
                }]
            },
            {
                "choices": [{
                    "message": {
                        "content": "I apologize, but I encountered an error when trying to get the weather information.",
                        "tool_calls": None
                    }
                }]
            }
        ]
        
        # 设置模拟工具执行器抛出异常
        mock_tool_executor = mock.MagicMock(spec=ToolExecutor)
        mock_tool_executor.execute_tool.side_effect = Exception("Weather service unavailable")
        
        # 创建组件
        orchestrator = Orchestrator()
        query_processor = QueryProcessor(orchestrator, mock_tool_executor)
        
        # 启动协调器
        await orchestrator.start()
        
        try:
            # 处理查询
            result = await query_processor.process_query("What's the weather in New York?")
            
            # 验证结果
            assert result == "I apologize, but I encountered an error when trying to get the weather information."
            
            # 验证调用
            mock_model.add_user_message.assert_called_once_with("What's the weather in New York?")
            assert mock_model.execute.call_count == 2
            mock_tool_executor.execute_tool.assert_called_once()
            # 确认添加了错误消息
            assert mock_model.add_tool_result.call_args[0][0] == "weather"
            assert "Error" in mock_model.add_tool_result.call_args[0][1]
        finally:
            await orchestrator.shutdown() 