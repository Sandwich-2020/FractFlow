import pytest
from FractalMCP.conversation.provider_adapters.openai_adapter import OpenAIHistoryAdapter
from FractalMCP.conversation.provider_adapters.deepseek_adapter import DeepSeekHistoryAdapter

class TestOpenAIHistoryAdapter:
    """测试OpenAI历史适配器"""
    
    def test_format_for_model_simple(self):
        """测试基本格式化"""
        adapter = OpenAIHistoryAdapter()
        
        # 创建测试消息
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        formatted = adapter.format_for_model(messages)
        
        # OpenAI适配器应该保持消息不变
        assert len(formatted) == 3
        assert formatted[0]["role"] == "system"
        assert formatted[0]["content"] == "You are a helpful assistant."
        assert formatted[1]["role"] == "user"
        assert formatted[1]["content"] == "Hello"
        assert formatted[2]["role"] == "assistant"
        assert formatted[2]["content"] == "Hi there!"
    
    def test_format_for_model_with_tool_calls(self):
        """测试带工具调用的格式化"""
        adapter = OpenAIHistoryAdapter()
        
        # 创建带工具调用的测试消息
        tool_calls = [{"name": "weather", "id": "call_id", "arguments": {"location": "New York"}}]
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the weather like?"},
            {"role": "assistant", "content": "Let me check that for you", "tool_calls": tool_calls},
            {"role": "tool", "tool_name": "weather", "content": "Sunny, 25°C", "tool_call_id": "call_id"}
        ]
        
        formatted = adapter.format_for_model(messages)
        
        # 验证格式化结果
        assert len(formatted) == 4
        assert formatted[2]["role"] == "assistant"
        assert "tool_calls" in formatted[2]
        assert formatted[2]["tool_calls"] == tool_calls
        
        assert formatted[3]["role"] == "tool"
        assert formatted[3]["content"] == "Sunny, 25°C"
        assert formatted[3]["tool_call_id"] == "call_id"

class TestDeepSeekHistoryAdapter:
    """测试DeepSeek历史适配器"""
    
    def test_format_for_model_simple(self):
        """测试基本格式化"""
        adapter = DeepSeekHistoryAdapter()
        
        # 创建测试消息
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        formatted = adapter.format_for_model(messages)
        
        # DeepSeek适配器应该保持基本消息不变
        assert len(formatted) == 3
        assert formatted[0]["role"] == "system"
        assert formatted[0]["content"] == "You are a helpful assistant."
        assert formatted[1]["role"] == "user"
        assert formatted[1]["content"] == "Hello"
        assert formatted[2]["role"] == "assistant"
        assert formatted[2]["content"] == "Hi there!"
    
    def test_format_for_model_with_tools(self):
        """测试带工具说明的格式化"""
        adapter = DeepSeekHistoryAdapter()
        
        # 创建测试消息
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What can you do?"}
        ]
        
        # 创建测试工具
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "weather",
                    "description": "Get the weather forecast",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state"
                            }
                        }
                    }
                }
            }
        ]
        
        formatted = adapter.format_for_model(messages, tools)
        
        # 验证工具描述被附加到了最后一条用户消息中
        assert len(formatted) == 2
        assert formatted[1]["role"] == "user"
        assert "Available tools:" in formatted[1]["content"]
        assert "weather" in formatted[1]["content"]
    
    def test_format_for_model_with_tool_results(self):
        """测试带工具结果的格式化"""
        adapter = DeepSeekHistoryAdapter()
        
        # 创建带工具结果的测试消息
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the weather like?"},
            {"role": "assistant", "content": "Let me check that for you"},
            {"role": "tool", "tool_name": "weather", "content": "Sunny, 25°C"}
        ]
        
        formatted = adapter.format_for_model(messages)
        
        # 验证工具结果被转换为用户消息
        assert len(formatted) == 4
        assert formatted[3]["role"] == "user"
        assert "Tool result from weather" in formatted[3]["content"]
        assert "Sunny, 25°C" in formatted[3]["content"]
    
    def test_ensure_alternating_messages(self):
        """测试确保消息交替"""
        adapter = DeepSeekHistoryAdapter()
        
        # 创建连续的用户消息
        messages = [
            {"role": "user", "content": "First user message"},
            {"role": "user", "content": "Second user message"}
        ]
        
        adapter._ensure_alternating_messages(messages)
        
        # 验证连续的用户消息被合并
        assert len(messages) == 1
        assert "First user message" in messages[0]["content"]
        assert "Second user message" in messages[0]["content"]
        
        # 创建连续的助手消息
        messages = [
            {"role": "assistant", "content": "First assistant message"},
            {"role": "assistant", "content": "Second assistant message"}
        ]
        
        adapter._ensure_alternating_messages(messages)
        
        # 验证连续的助手消息被合并
        assert len(messages) == 1
        assert "First assistant message" in messages[0]["content"]
        assert "Second assistant message" in messages[0]["content"]
    
    def test_format_tools_description(self):
        """测试格式化工具描述"""
        adapter = DeepSeekHistoryAdapter()
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Perform arithmetic operations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"},
                            "operation": {"type": "string", "description": "Operation to perform"}
                        }
                    }
                }
            }
        ]
        
        description = adapter._format_tools_description(tools)
        
        # 验证描述包含预期的内容
        assert "calculator" in description
        assert "Perform arithmetic operations" in description
        assert "a (number)" in description
        assert "b (number)" in description
        assert "operation (string)" in description 