"""
集成测试的 Pytest 共享测试配置。

提供共享的 Fixtures 和辅助函数，用于集成测试。
"""
import sys
import pytest
import asyncio
from typing import Dict, Any, List, Generator

# 确保可以从测试中导入源代码
sys.path.append('.')

@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    创建一个事件循环并在测试完成后关闭。
    用于 pytest 异步测试。
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_tools() -> List[Dict[str, Any]]:
    """
    提供模拟的工具定义列表。
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "weather",
                "description": "Get the current weather in a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "Perform a calculation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The calculation to perform, e.g. 2+2"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    ] 