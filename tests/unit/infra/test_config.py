import os
import json
import pytest
import tempfile
from FractFlow.infra.config import ConfigManager

class TestConfigManager:
    """测试配置管理器"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2
    
    def test_get_default_value(self):
        """测试获取默认值"""
        config = ConfigManager()
        # 使用一个不存在的键，应该返回默认值
        assert config.get('non_existent_key', 'default_value') == 'default_value'
    
    def test_set_and_get(self):
        """测试设置和获取值"""
        config = ConfigManager()
        # 设置一个新值
        config.set('test.key', 'test_value')
        # 获取设置的值
        assert config.get('test.key') == 'test_value'
        
        # 设置嵌套值
        config.set('nested.key.subkey', 'nested_value')
        assert config.get('nested.key.subkey') == 'nested_value'
    
    def test_load_from_file(self):
        """测试从文件加载配置"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            config_data = {
                'test': {'file_key': 'file_value'},
                'agent': {'max_iterations': 5}
            }
            json.dump(config_data, temp_file)
            temp_file_name = temp_file.name
        
        try:
            # 加载配置
            config = ConfigManager()
            config.load_from_file(temp_file_name)
            
            # 验证配置已加载
            assert config.get('test.file_key') == 'file_value'
            assert config.get('agent.max_iterations') == 5
        finally:
            # 清理临时文件
            os.unlink(temp_file_name)
    
    def test_deep_merge(self):
        """测试深度合并配置"""
        config = ConfigManager()
        
        # 设置初始值
        config.set('merge_test.key1', 'value1')
        config.set('merge_test.nested.key2', 'value2')
        
        # 创建要合并的数据
        merge_data = {
            'merge_test': {
                'key1': 'new_value1',  # 这应该被替换
                'nested': {
                    'key2': 'new_value2',  # 这应该被替换
                    'key3': 'value3'      # 这应该被添加
                },
                'key4': 'value4'          # 这应该被添加
            }
        }
        
        # 执行合并
        config._deep_merge(config._config, merge_data)
        
        # 验证合并结果
        assert config.get('merge_test.key1') == 'new_value1'
        assert config.get('merge_test.nested.key2') == 'new_value2'
        assert config.get('merge_test.nested.key3') == 'value3'
        assert config.get('merge_test.key4') == 'value4' 