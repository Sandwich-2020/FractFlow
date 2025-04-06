import pytest
import unittest.mock as mock
import os
import asyncio
from src.core.orchestrator import Orchestrator
from src.models.base_model import BaseModel
from src.infra.error_handling import ConfigurationError

class TestOrchestrator:
    """测试协调器"""
    
    @mock.patch('src.core.orchestrator.create_model')
    def test_initialization(self, mock_create_model):
        """测试初始化"""
        # 设置模拟模型
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        
        # 创建协调器
        orchestrator = Orchestrator(
            system_prompt="Test prompt",
            tool_configs={"test_tool": "/path/to/tool.py"},
            provider="test_provider"
        )
        
        # 验证模型创建
        mock_create_model.assert_called_once_with("Test prompt", "test_provider")
        assert orchestrator.model is mock_model
        assert orchestrator.tool_configs == {"test_tool": "/path/to/tool.py"}
    
    @mock.patch('src.core.orchestrator.create_model')
    def test_get_model(self, mock_create_model):
        """测试获取模型"""
        # 设置模拟模型
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        
        # 创建协调器
        orchestrator = Orchestrator()
        
        # 获取模型
        model = orchestrator.get_model()
        
        # 验证模型
        assert model is mock_model
    
    @mock.patch('src.core.orchestrator.create_model')
    def test_register_tool_provider_before_start(self, mock_create_model):
        """测试在启动前注册工具提供者"""
        # 设置模拟模型
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        
        # 创建协调器
        orchestrator = Orchestrator()
        
        # 注册工具提供者
        orchestrator.register_tool_provider("test_tool", "/path/to/tool.py")
        
        # 验证工具配置
        assert orchestrator.tool_configs == {"test_tool": "/path/to/tool.py"}
    
    @mock.patch('src.core.orchestrator.create_model')
    @mock.patch('src.mcp.launcher.MCPLauncher')
    @mock.patch('src.mcp.tool_loader.MCPToolLoader')
    async def test_start(self, mock_tool_loader_class, mock_launcher_class, mock_create_model):
        """测试启动"""
        # 设置模拟对象
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        mock_launcher = mock.MagicMock()
        mock_launcher_class.return_value = mock_launcher
        
        # 使launch_all返回一个协程
        future = asyncio.Future()
        future.set_result(None)
        mock_launcher.launch_all.return_value = future
        
        mock_tool_loader = mock.MagicMock()
        mock_tool_loader_class.return_value = mock_tool_loader
        
        # 创建协调器
        orchestrator = Orchestrator(
            tool_configs={"test_tool": "/path/to/tool.py"}
        )
        
        # 启动协调器
        await orchestrator.start()
        
        # 验证启动过程
        mock_launcher_class.assert_called_once()
        mock_tool_loader_class.assert_called_once()
        assert orchestrator.launcher is mock_launcher
        assert orchestrator.tool_loader is mock_tool_loader
        mock_launcher.launch_all.assert_called_once()
    
    @mock.patch('src.core.orchestrator.create_model')
    @mock.patch('src.mcp.launcher.MCPLauncher')
    async def test_shutdown(self, mock_launcher_class, mock_create_model):
        """测试关闭"""
        # 设置模拟对象
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        mock_launcher = mock.MagicMock()
        mock_launcher_class.return_value = mock_launcher
        
        # 使launch_all和shutdown返回协程
        launch_future = asyncio.Future()
        launch_future.set_result(None)
        mock_launcher.launch_all.return_value = launch_future
        
        shutdown_future = asyncio.Future()
        shutdown_future.set_result(None)
        mock_launcher.shutdown.return_value = shutdown_future
        
        # 创建协调器
        orchestrator = Orchestrator()
        
        # 启动和关闭协调器
        await orchestrator.start()
        await orchestrator.shutdown()
        
        # 验证关闭过程
        mock_launcher.shutdown.assert_called_once()
    
    @mock.patch('src.core.orchestrator.create_model')
    @mock.patch('src.mcp.launcher.MCPLauncher')
    @mock.patch('src.mcp.tool_loader.MCPToolLoader')
    async def test_get_available_tools(self, mock_tool_loader_class, mock_launcher_class, mock_create_model):
        """测试获取可用工具"""
        # 设置模拟对象
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        mock_launcher = mock.MagicMock()
        mock_launcher_class.return_value = mock_launcher
        
        # 使launch_all返回协程
        launch_future = asyncio.Future()
        launch_future.set_result(None)
        mock_launcher.launch_all.return_value = launch_future
        
        mock_tool_loader = mock.MagicMock()
        mock_tool_loader_class.return_value = mock_tool_loader
        
        # 设置模拟客户端和工具
        mock_session = mock.MagicMock()
        # 正确设置client_pool.clients
        mock_launcher.client_pool.clients = {"test_client": mock_session}
        
        # 使load_tools返回协程
        tools_future = asyncio.Future()
        mock_tools = [{"type": "function", "function": {"name": "test_tool"}}]
        tools_future.set_result(mock_tools)
        mock_tool_loader.load_tools.return_value = tools_future
        
        # 创建协调器
        orchestrator = Orchestrator()
        
        # 启动协调器
        await orchestrator.start()
        
        # 获取可用工具
        tools = await orchestrator.get_available_tools()
        
        # 验证工具加载
        mock_tool_loader.load_tools.assert_called_once_with(mock_session)
        assert tools == mock_tools
    
    @mock.patch('src.core.orchestrator.create_model')
    async def test_get_available_tools_before_start(self, mock_create_model):
        """测试在启动前获取可用工具"""
        # 设置模拟模型
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        
        # 创建协调器
        orchestrator = Orchestrator()
        
        # 获取可用工具应该抛出异常
        with pytest.raises(ConfigurationError) as excinfo:
            await orchestrator.get_available_tools()
        
        # 验证错误消息
        assert "Orchestrator not started" in str(excinfo.value)
    
    @mock.patch('src.core.orchestrator.create_model')
    @mock.patch('os.path.exists')
    def test_register_tools_from_config(self, mock_exists, mock_create_model):
        """测试从配置注册工具"""
        # 设置模拟对象
        mock_model = mock.MagicMock(spec=BaseModel)
        mock_create_model.return_value = mock_model
        mock_exists.return_value = True
        
        # 创建协调器
        orchestrator = Orchestrator()
        
        # 模拟工具配置
        tool_configs = {
            "tool1": "/path/to/tool1.py",
            "tool2": "/path/to/tool2.py"
        }
        
        # 注册工具
        orchestrator.register_tools_from_config(tool_configs)
        
        # 验证工具配置
        assert "tool1" in orchestrator.tool_configs
        assert "tool2" in orchestrator.tool_configs
        assert orchestrator.tool_configs["tool1"] == "/path/to/tool1.py"
        assert orchestrator.tool_configs["tool2"] == "/path/to/tool2.py" 