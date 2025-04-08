# FractFlow

FractFlow 是一种分形式智能架构，它将智能拆解为可嵌套的 Agent-Tool 单元，通过递归组合构建出动态演化的分布式心智系统。

## 设计思想

FractFlow 是一种分形式智能架构，它将智能拆解为可嵌套的 Agent-Tool 单元，通过递归组合构建出动态演化的分布式心智系统。

每个智能体（Agent）不仅具有认知能力，也具备调用其他 Agent 的能力，从而形成一种自指、自组织、自适应的智能流。

类似章鱼那样的「多大脑」协作结构，FractFlow 并不依赖中心化控制，而是通过模块化智能的组合与协调，实现一种结构可塑、行为可生长的分布式智能形态。

## 安装

### 方法一：本地安装

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 方法二：构建并安装包

```bash
python -m build 
```

然后你会获得一个 dist 文件夹，可以通过以下命令安装:

```bash
uv pip install dist/FractFlow-0.1.0-py3-none-any.whl
```

## 快速开始

首先需要获取语言模型的 API Key。目前支持 DeepSeek 和 Qwen 模型。优先用 DeepSeek 模型, Qwen 还没完整测试。

### 配置 API Key

在根目录下创建一个 .env 文件，并添加如下内容：

```bash
DEEPSEEK_API_KEY=your_api_key
QWEN_API_KEY=your_api_key
```

### 创建和运行一个简单的 Agent

以下是一个基本的示例，展示如何创建和使用 FractFlow Agent：

```python
import asyncio
import os
from dotenv import load_dotenv
from FractFlow.agent import Agent

async def main():
    # 加载环境变量
    load_dotenv()
    
    # 创建 Agent
    agent = Agent()
    config = agent.get_config()
    # 可以按需求重写默认配置
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['deepseek']['model'] = 'deepseek-chat'
    config['agent']['max_iterations'] = 100
    agent.set_config(config)
    
    # 添加工具
    agent.add_tool("./tools/weather/forecast.py")
    
    # 初始化 Agent
    await agent.initialize()
    
    try:
        # 处理用户查询
        result = await agent.process_query("我想知道北京的天气预报")
        print(f"Agent: {result}")
    finally:
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## 如何编写工具

FractFlow 使用 MCP 协议来定义工具。工具可以是单独的 Python 文件，按照 MCP server 的协议编写。

### 工具示例

以下是一个天气预报工具的示例（参考 `tools/forecast.py`）：

```python
from typing import Any, Dict
import httpx
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 服务器
mcp = FastMCP("weather")

# API 常量
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """向 NWS API 发起请求并进行错误处理"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """获取指定位置的天气预报
    
    Args:
        latitude: 位置的纬度
        longitude: 位置的经度
    """
    # 获取预报网格端点
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    
    if not points_data:
        return "无法获取此位置的预报数据。"
    
    # 从点响应中获取预报 URL
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    
    if not forecast_data:
        return "无法获取详细预报。"
    
    # 将周期格式化为可读的预报
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # 只显示接下来的 5 个时段
        forecast = f"""
{period['name']}:
温度: {period['temperature']}°{period['temperatureUnit']}
风: {period['windSpeed']} {period['windDirection']}
预报: {period['detailedForecast']}
"""
        forecasts.append(forecast)
    
    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    # 初始化并运行服务器
    mcp.run(transport='stdio')
```

### 工具开发规范

1. 使用 `FastMCP` 类创建工具服务器
2. 使用 `@mcp.tool()` 装饰器定义工具函数
3. 提供清晰的函数文档和参数说明
4. 工具函数应该是异步的 (`async def`)
5. 在 `if __name__ == "__main__":` 块中运行服务器

## 使用 FractFlow 库

以下是如何使用 FractFlow 库的更完整示例（参考 `run_simple_example.py`）：

```python
import asyncio
import os
from dotenv import load_dotenv
from FractFlow.agent import Agent

async def main():
    # 加载环境变量
    load_dotenv()
    
    # 创建 Agent
    agent = Agent()
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['deepseek']['model'] = 'deepseek-chat'
    config['qwen']['api_key'] = os.getenv('QWEN_API_KEY')
    config['agent']['max_iterations'] = 100
    agent.set_config(config)
    
    # 添加工具
    if os.path.exists("./tools/weather/forecast.py"):
        agent.add_tool("./tools/weather/forecast.py")
        print("Added weather tool")
    
    # 初始化 Agent
    print("Initializing agent...")
    await agent.initialize()
    
    try:
        # 交互式聊天循环
        print("Agent chat started. Type 'exit', 'quit', or 'bye' to end the conversation.")
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ('exit', 'quit', 'bye'):
                break
                
            print("\n thinking... \n", end="")
            result = await agent.process_query(user_input)
            print("Agent: {}".format(result))
    finally:
        # 优雅地关闭 Agent
        await agent.shutdown()
        print("\nAgent chat ended.")

if __name__ == "__main__":
    asyncio.run(main())
```

### 主要 API 方法

- `agent = Agent()` - 创建一个新的 Agent 实例
- `config = agent.get_config()` - 获取当前配置
- `agent.set_config(config)` - 设置配置
- `agent.add_tool(tool_path)` - 添加工具到 Agent
- `await agent.initialize()` - 初始化 Agent
- `result = await agent.process_query(user_input)` - 处理用户查询
- `await agent.shutdown()` - 关闭 Agent

## 高级用法：Agent 作为工具

FractFlow 的一个强大特性是 Agent 本身可以作为更智能的工具被其他 Agent 使用，形成一种分形架构。以下是一个示例（参考 `fractal_weather_tool.py`）：

```python
import asyncio
import os
import sys
from dotenv import load_dotenv
from FractFlow.agent import Agent
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fractal weather")

@mcp.tool()
async def weather_agent(user_input: str) -> str:
    """
    这个函数接收用户输入并返回天气预报。
    Args:
        user_input: 用户的输入
    Returns:
        天气预报结果
    """
    # 加载环境变量
    load_dotenv()
    
    # 创建 Agent
    agent = Agent()
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['deepseek']['model'] = 'deepseek-chat'
    config['agent']['max_iterations'] = 100
    agent.set_config(config)
    
    # 添加工具
    if os.path.exists("./tools/weather/forecast.py"):
        agent.add_tool("./tools/weather/forecast.py")
        print("Added weather tool")
    
    # 初始化 Agent
    await agent.initialize()
    
    try:
        # 处理用户查询
        result = await agent.process_query(user_input)
    finally:
        # 关闭 Agent
        await agent.shutdown()
    
    return result

if __name__ == "__main__":
    # 初始化并运行服务器
    mcp.run(transport='stdio')
```

这种方法允许你创建一个专门的 Agent 工具，它可以被其他 Agent 调用，从而形成分形智能结构。高级 Agent 可以将任务分解给专门的 Agent，每个专门的 Agent 又可以使用自己的工具集。
