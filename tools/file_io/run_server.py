import asyncio
import os
import sys
import logging
import argparse

import os.path as osp
# Add the project root directory to the Python path
project_root = osp.abspath(osp.join(osp.dirname(__file__), '..'))
sys.path.append(project_root)

# Import the FractalFlow Agent
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager
from FractFlow.infra.logging_utils import setup_logging, get_logger

# 设置日志
setup_logging(level=logging.INFO)


async def create_agent():
    """创建并初始化Agent"""
    # Create a new agent
    agent = Agent('file_io_agent')  # No need to specify provider here if it's in config
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    # config['agent']['custom_system_prompt'] = '你会用萌萌哒的语气回复'
    config['deepseek']['model'] = 'deepseek-chat'
    # You can modify configuration values directly
    config['agent']['max_iterations'] = 5  # Properly set as nested value
    # 4. Set configuration loaded from environment
    agent.set_config(config)
    
    # Add tools to the agent
    # agent.add_tool("./tools/ComfyUITool.py")
    # agent.add_tool("./tools/VisualQestionAnswer.py")
    agent.add_tool("./tools/file_io/src/server.py")
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    return agent


async def interactive_mode(agent):
    """交互式聊天模式"""
    print("Agent chat started. Type 'exit', 'quit', or 'bye' to end the conversation.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ('exit', 'quit', 'bye'):
            break
            
        print("\n thinking... \n", end="")
        result = await agent.process_query(user_input)
        print("Agent: {}".format(result))


async def single_query_mode(agent, query):
    """一次性执行模式"""
    print(f"Processing query: {query}")
    print("\n thinking... \n", end="")
    result = await agent.process_query(query)
    print("Result: {}".format(result))
    return result


async def main():
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='Run File I/O Tool Server')
    parser.add_argument('--user_query', type=str, help='单次查询模式：直接处理这个查询并返回结果')
    args = parser.parse_args()
    
    # 创建Agent
    agent = await create_agent()
    
    try:
        if args.user_query:
            # 单次查询模式
            await single_query_mode(agent, args.user_query)
        else:
            # 交互式聊天模式
            await interactive_mode(agent)
    finally:
        # 关闭Agent
        await agent.shutdown()
        print("\nAgent session ended.")


if __name__ == "__main__":
    asyncio.run(main()) 