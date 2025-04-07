import pytest
import unittest.mock as mock
from src.models.factory import create_model
from src.models.deepseek_model import DeepSeekModel
from src.models.qwen_model import QwenModel

class TestModelFactory:
    """测试模型工厂"""
    
    @mock.patch('src.models.deepseek_model.OpenAI')
    def test_create_model_deepseek(self, mock_openai):
        """测试创建DeepSeek模型"""
        # 使用明确的提供者参数
        model = create_model(system_prompt="Test prompt", provider="deepseek")
        assert isinstance(model, DeepSeekModel)
        # 验证OpenAI客户端被正确初始化
        mock_openai.assert_called()
    
    @mock.patch('src.models.qwen_model.OpenAI')
    def test_create_model_qwen(self, mock_openai):
        """测试创建QWEN模型"""
        # 使用明确的提供者参数
        model = create_model(system_prompt="Test prompt", provider="qwen")
        assert isinstance(model, QwenModel)
        # 验证OpenAI客户端被正确初始化
        mock_openai.assert_called()
    
    @mock.patch('src.models.factory.config')
    @mock.patch('src.models.deepseek_model.OpenAI')
    def test_create_model_from_config(self, mock_openai, mock_config):
        """测试从配置创建模型"""
        # 配置返回deepseek作为提供者
        mock_config.get.return_value = "deepseek"
        
        # 不提供提供者参数，应该从配置获取
        model = create_model(system_prompt="Test prompt")
        assert isinstance(model, DeepSeekModel)
        
        # 验证配置调用
        mock_config.get.assert_any_call('agent.provider', 'openai')
        # 验证OpenAI客户端被正确初始化
        mock_openai.assert_called()
    
    def test_create_model_openai_not_implemented(self):
        """测试OpenAI模型尚未实现"""
        with pytest.raises(NotImplementedError) as excinfo:
            create_model(system_prompt="Test prompt", provider="openai")
        
        # 验证错误消息
        assert "OpenAI provider support is not yet implemented" in str(excinfo.value)
    
    def test_create_model_unsupported_provider(self):
        """测试不支持的提供者"""
        with pytest.raises(ValueError) as excinfo:
            create_model(provider="unsupported_provider")
        
        # 验证错误消息
        assert "Unsupported AI provider" in str(excinfo.value) 