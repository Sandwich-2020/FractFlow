#!/usr/bin/env python3
"""
run_simple_example_ui.py
Description: Example script demonstrating how to use the FractFlow UI
"""

import asyncio
import os
from dotenv import load_dotenv

from FractFlow.agent import Agent
from FractFlow.ui.ui import FractFlowUI

async def main():
    # Load environment variables
    load_dotenv()
    
    # Create and configure agent
    agent = Agent()
    config = agent.get_config()
    config['agent']['provider'] = 'qwen'
    config['agent']['custom_system_prompt'] = '你会用萌萌哒的语气回复'
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['deepseek']['model'] = 'deepseek-chat'
    config['qwen']['api_key'] = os.getenv('QWEN_API_KEY')
    config['qwen']['base_url'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    config['agent']['max_iterations'] = 100
    
    # Set configuration
    agent.set_config(config)
    
    # Add tools
    agent.add_tool("./tools/forecast.py")
    
    try:
        # Create UI
        ui = FractFlowUI(agent)
        
        # Initialize agent
        await ui.initialize()
        
        # Run the UI server
        FractFlowUI.run()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Shutdown the agent
        await agent.shutdown()

if __name__ in {"__main__", "__mp_main__"}:
    asyncio.run(main())