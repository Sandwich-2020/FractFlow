import asyncio
import os
import sys
import logging
import argparse
from FractFlow.infra.logging_utils import setup_logging

# Import the FractFlow Agent
from FractFlow.agent import Agent

# System prompt for the AI-enhanced version
SYSTEM_PROMPT = """
## 🧠 你是一个图文 Markdown 内容生成 Agent

你的职责是撰写结构化的 Markdown 文章，并在适当位置自动插入相关插图，最终生成一篇完整、图文并茂的 Markdown 文件。

---

## 🔁 工作流（循环执行）

### 1. 规划阶段（仅一次）

* 明确主题、结构、段落划分、图像需求
* 在内部完成规划，**不输出**

---

### 2. 段落生成流程（每段循环）

#### 2.1 撰写段落

* 撰写该段 Markdown 内容，结构清晰、语言自然，故事完整，字数不小于500字。
* 在合适位置插入图像路径引用，如：
  `![说明](images/sectionX-figY.png)`
* 内容必须**直接写入 Markdown 文件**，**不得输出到 response 中**

#### 2.2 生成插图

* 根据该段上下文，为引用的路径生成图像
* 图像应与引用路径匹配，保存至 `images/` 子目录

#### 2.3 路径一致性检查

* 检查当前段落图像路径是否：

  * 属于 `images/` 目录
  * 与实际文件匹配
  * 唯一、不重复

---

### 3. 进入下一段

* 重复段落撰写、插图生成、路径校验，直到整篇文章完成

---

## 📁 文件结构约定

* 文章主文件为 Markdown 格式
* 图像命名应基于段落结构，如 `section2-fig1.png`
* 如果没有特别指定目录的话，请你把文章保存到“output/visual_article_generator/”目录下，每一个项目起一个新的文件夹，文件夹名称为项目名称。结构如下：
```
output/visual_article_generator/
├── project1/
│   ├── article.md
│   └── images/
```

---

## 🚫 输出规范（必须遵守）

* 不得输出 Markdown 正文或图像信息到 response 中
* 所有正文和图像操作都应**直接执行、写入对应文件和目录**
* **你不是讲述者，而是操作执行者**。只做事，不解释

"""

async def create_agent(mode_type):
    """Create and initialize the Agent with appropriate tools"""
    # Create a new agent
    agent = Agent('Visual Article Generator')
    
    # Configure the agent
    config = agent.get_config()
    if mode_type == "single query":
        SYSTEM_PROMPT_NOW = SYSTEM_PROMPT + "\n SINGLE QUERY MODE, DONOT ASK USER FOR ANYTHING"
    else:
        SYSTEM_PROMPT_NOW = SYSTEM_PROMPT
    # You can customize the config here if needed
    config['agent']['custom_system_prompt'] = SYSTEM_PROMPT_NOW
    config['agent']['max_iterations'] = 50
    agent.set_config(config)
    
    # Get the tool path based on the use_ai_server flag
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the appropriate tool to the agent
    agent.add_tool('tools/file_io2/file_io.py', 'file_io')
    agent.add_tool('tools/gpt_imagen/server.py', 'gpt_imagen')
    
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    return agent

async def interactive_mode(agent):
    """Interactive chat mode with multi-turn conversation support"""
    print("\nGPT Image Generator Tool Interactive Mode")
    print("Type 'exit', 'quit', or 'bye' to end the conversation.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ('exit', 'quit', 'bye'):
            break
        
        print("\nProcessing...\n")
        result = await agent.process_query(user_input)
        print(f"Agent: {result}")

async def single_query_mode(agent, query):
    """One-time execution mode for a single query"""
    print(f"Processing query: {query}")
    print("\nProcessing...\n")
    result = await agent.process_query(query)
    print(f"Result: {result}")
    return result

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run GPT Image Generator Tool Server')
    parser.add_argument('-q', '--query', type=str, help='Single query mode: process this query and exit')
    parser.add_argument('-ui', '--ui', action='store_true', help='Run UI mode')
    args = parser.parse_args()
    
    # Determine which server to use and display info
    mode_type = "single query" if args.query else "interactive"

    # Create and initialize the agent
    agent = await create_agent(mode_type)
    
    if args.ui:
        try:
            from FractFlow.ui.ui import FractFlowUI
            ui = FractFlowUI(agent)
            await ui.initialize()
            FractFlowUI.run()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Clean up and shut down
            await agent.shutdown()
            print("\nAgent session ended.")
    else:
        try:
            if args.query:
                # Single query mode
                await single_query_mode(agent, args.query)
            else:
                # Interactive chat mode
                await interactive_mode(agent)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Clean up and shut down
            await agent.shutdown()
            print("\nAgent session ended.")

if __name__ in {"__main__", "__mp_main__"}:
    # Set basic logging
    setup_logging(level=logging.WARN)
    # Run the async main function
    asyncio.run(main()) 