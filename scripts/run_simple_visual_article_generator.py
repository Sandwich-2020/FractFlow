"""
Web Search Tool Server Runner

This module provides the entry point for starting the Web Search Tool server.
It can be run in two modes:
1. Interactive chat mode - continuous processing of user queries until exit
2. Single query mode - processing a single query and then exiting

The module initializes a FractFlow agent with the Web Search tool and
handles user interactions according to the chosen mode.

Author: Xinli Xu (xxu068@connect.hkust-gz.edu.cn) - Envision Lab
Date: 2025-04-28
License: MIT License
"""

import asyncio
import os
import sys
import logging
import argparse
from dotenv import load_dotenv

import os.path as osp
# Add the project root directory to the Python path
project_root = osp.abspath(osp.join(osp.dirname(__file__), '../..'))
sys.path.append(project_root)

# Import the FractFlow Agent
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager
from FractFlow.infra.logging_utils import setup_logging, get_logger

# Setup logging
setup_logging(level=logging.DEBUG)


async def create_agent():
    """Create and initialize the Agent"""
    load_dotenv()
    # Create a new agent
    agent = Agent('Image_Article_Application')  # No need to specify provider here if it's in config
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'

    config['agent']['custom_system_prompt'] = """
你是一个图文 Markdown 内容生成 Agent，具备两个核心能力：

1. **写文章**：结构清晰、语言通顺，用 Markdown 格式输出
2. **生图**：在适当位置，生成一张对应的插图，并嵌入文章中

---

### ✍️ 写文章规则

* 请直接调用工具把文章写在文件里，不要回答在response 里。
* 文章是用markdown 语法写的。里面在适当的地方加上插图，插图应该引用其相对路径（放到 images/ 目录下）。以便未来在路径中生成插图。

---

### 🖼 插图生成规则

* 对每张图：

  * 规划路径：插图位置应该与写文章的时候，留下位置一致。
  * 调用工具generate_image_with_comfyui生成图像.

---
请一次性生成所有的文字和插图。

在每次生成前后，应该检查一下当前路径，生成完成后，也应该检查。

路径尤其容易错，请在生成的时候，务必检查。

     """
    config['deepseek']['model'] = 'deepseek-chat'
    # You can modify configuration values directly
    config['agent']['max_iterations'] = 20  # Properly set as nested value
    # 4. Set configuration loaded from environment
    agent.set_config(config)
    
    # Add tools to the agent
    agent.add_tool("./tools/ComfyUITool.py", "image_generation_tool")
    agent.add_tool("./tools/editor/server.py", "editor_tool")
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    return agent


async def interactive_mode(agent):
    """Interactive chat mode"""
    print("Agent chat started. Type 'exit', 'quit', or 'bye' to end the conversation.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ('exit', 'quit', 'bye'):
            break
            
        print("\n thinking... \n", end="")
        result = await agent.process_query(user_input)
        print("Agent: {}".format(result))


async def single_query_mode(agent, query):
    """One-time execution mode"""
    print(f"Processing query: {query}")
    print("\n thinking... \n", end="")
    result = await agent.process_query(query)
    print("Result: {}".format(result))
    return result


async def main():
    # Command line argument parsing
    parser = argparse.ArgumentParser(description='Run Web Search Tool Server')
    parser.add_argument('--user_query', type=str, help='Single query mode: process this query and exit')
    args = parser.parse_args()
    
    # Create Agent
    agent = await create_agent()
    
    try:
        if args.user_query:
            # Single query mode
            await single_query_mode(agent, args.user_query)
        else:
            # Interactive chat mode
            await interactive_mode(agent)
    finally:
        # Close Agent
        await agent.shutdown()
        print("\nAgent session ended.")


if __name__ == "__main__":
    asyncio.run(main()) 