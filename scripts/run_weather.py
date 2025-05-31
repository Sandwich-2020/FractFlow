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
You are a helpful assistant that can answer questions about the weather. 
Your tool can only access the weather of US. If the user asks about the weather of other countries, you should say you don't know.
The weather tool requires latitude and longitude as input. You can estimate them based on your knowledge.
"""

async def create_agent(mode_type):
    """Create and initialize the Agent with appropriate tools"""
    # Create a new agent
    agent = Agent('Weather_Agent')
    
    # Configure the agent
    config = agent.get_config()
    if mode_type == "single query":
        SYSTEM_PROMPT_NOW = SYSTEM_PROMPT + "\n SINGLE QUERY MODE, DONOT ASK USER FOR ANYTHING"
    else:
        SYSTEM_PROMPT_NOW = SYSTEM_PROMPT
    # You can customize the config here if needed
    config['agent']['custom_system_prompt'] = SYSTEM_PROMPT_NOW
    agent.set_config(config)
    
    # Get the tool path based on the use_ai_server flag
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the appropriate tool to the agent
    agent.add_tool('tools/forecast.py', 'forecast')
    
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