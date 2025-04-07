import pytest
from FractalMCP.conversation.base_history import ConversationHistory

class TestConversationHistory:
    """测试对话历史管理"""
    
    def test_initialization_with_system_prompt(self):
        """测试使用系统提示初始化"""
        system_prompt = "You are a helpful assistant."
        history = ConversationHistory(system_prompt)
        
        messages = history.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == system_prompt
    
    def test_initialization_without_system_prompt(self):
        """测试不使用系统提示初始化"""
        history = ConversationHistory()
        
        messages = history.get_messages()
        assert len(messages) == 0
    
    def test_add_user_message(self):
        """测试添加用户消息"""
        history = ConversationHistory()
        user_message = "Hello, how are you?"
        
        history.add_user_message(user_message)
        
        messages = history.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == user_message
    
    def test_add_assistant_message(self):
        """测试添加助手消息"""
        history = ConversationHistory()
        assistant_message = "I'm doing well, thank you!"
        
        # 不带工具调用
        history.add_assistant_message(assistant_message)
        
        messages = history.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "assistant"
        assert messages[0]["content"] == assistant_message
        assert "tool_calls" not in messages[0]
        
        # 带工具调用
        tool_calls = [{"name": "weather", "arguments": {"location": "New York"}}]
        history.add_assistant_message("Check the weather", tool_calls)
        
        messages = history.get_messages()
        assert len(messages) == 2
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Check the weather"
        assert "tool_calls" in messages[1]
        assert messages[1]["tool_calls"] == tool_calls
    
    def test_add_tool_result(self):
        """测试添加工具结果"""
        history = ConversationHistory()
        tool_name = "weather"
        result = "It's sunny in New York, 25°C"
        tool_call_id = "call_123456"
        
        # 带工具调用ID
        history.add_tool_result(tool_name, result, tool_call_id)
        
        messages = history.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
        assert messages[0]["tool_name"] == tool_name
        assert messages[0]["content"] == result
        assert messages[0]["tool_call_id"] == tool_call_id
        
        # 不带工具调用ID
        history.add_tool_result("calculator", "42")
        
        messages = history.get_messages()
        assert len(messages) == 2
        assert messages[1]["role"] == "tool"
        assert messages[1]["tool_name"] == "calculator"
        assert messages[1]["content"] == "42"
        assert "tool_call_id" not in messages[1]
    
    def test_get_last_message(self):
        """测试获取最后一条消息"""
        history = ConversationHistory()
        
        # 空历史应该返回None
        assert history.get_last_message() is None
        
        # 添加一条消息
        history.add_user_message("First message")
        assert history.get_last_message()["content"] == "First message"
        
        # 添加第二条消息
        history.add_assistant_message("Second message")
        assert history.get_last_message()["content"] == "Second message"
    
    def test_clear(self):
        """测试清除历史"""
        history = ConversationHistory("System prompt")
        
        # 添加一些消息
        history.add_user_message("User message")
        history.add_assistant_message("Assistant message")
        
        # 清除历史
        history.clear()
        
        # 应该只保留系统消息
        messages = history.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
    
    def test_format_debug_output(self):
        """测试格式化调试输出"""
        history = ConversationHistory("System prompt")
        history.add_user_message("User message")
        history.add_assistant_message("Assistant message", [{"name": "tool_name"}])
        history.add_tool_result("tool_name", "Tool result")
        
        debug_output = history.format_debug_output()
        
        # 简单验证输出包含所有消息
        assert "SYSTEM" in debug_output
        assert "USER" in debug_output
        assert "ASSISTANT" in debug_output
        assert "TOOL" in debug_output 