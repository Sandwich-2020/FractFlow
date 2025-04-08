import pytest
import unittest.mock as mock
import asyncio
from FractFlow.core.tool_executor import ToolExecutor
from FractFlow.infra.error_handling import ToolExecutionError

class TestToolExecutor:
    """测试工具执行器"""
    
    @mock.patch('FractalFlow.mcp.client_pool')
    async def test_execute_tool_success(self, mock_client_pool):
        """测试成功执行工具"""
        # 设置模拟客户端池
        future = asyncio.Future()
        future.set_result("Tool execution result")
        mock_client_pool.call.return_value = future
        
        # 创建工具执行器
        executor = ToolExecutor()
        
        # 执行工具
        result = await executor.execute_tool("test_tool", {"param": "value"})
        
        # 验证结果
        assert result == "Tool execution result"
        mock_client_pool.call.assert_called_once_with("test_tool", {"param": "value"})
    
    @mock.patch('FractalFlow.mcp.client_pool')
    async def test_execute_tool_failure(self, mock_client_pool):
        """测试工具执行失败"""
        # 设置模拟客户端池抛出异常
        mock_client_pool.call.side_effect = Exception("Call failed")
        
        # 创建工具执行器
        executor = ToolExecutor()
        
        # 执行工具应该抛出ToolExecutionError
        with pytest.raises(ToolExecutionError) as excinfo:
            await executor.execute_tool("test_tool", {"param": "value"})
        
        # 验证错误消息
        assert "Failed to execute tool" in str(excinfo.value)
        mock_client_pool.call.assert_called_once_with("test_tool", {"param": "value"})
    
    @mock.patch('FractalFlow.mcp.client_pool')
    @mock.patch('FractalFlow.core.tool_executor.logger')
    async def test_execute_tool_logs_error(self, mock_logger, mock_client_pool):
        """测试工具执行错误日志记录"""
        # 设置模拟客户端池抛出异常
        mock_client_pool.call.side_effect = Exception("Call failed")
        
        # 创建工具执行器
        executor = ToolExecutor()
        
        # 执行工具并捕获异常
        with pytest.raises(ToolExecutionError):
            await executor.execute_tool("test_tool", {"param": "value"})
        
        # 验证错误被记录
        mock_logger.error.assert_called_once()
        assert "Error executing tool" in mock_logger.error.call_args[0][0] 