#!/usr/bin/env python3
"""
fractflow_nicegui.py
Description: Web interface for FractalFlow Agent using NiceGUI
"""

import asyncio
import os
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from dotenv import load_dotenv
from nicegui import ui

# Import the FractalFlow Agent
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

# Global variables
messages: List[Tuple[str, str, str, str]] = []
agent = None

# Load environment variables
load_dotenv()

@ui.refreshable
def chat_messages(own_id: str) -> None:
    if messages:
        for user_id, avatar, text, stamp in messages:
            ui.chat_message(text=text, stamp=stamp, avatar=avatar, sent=own_id == user_id)
    else:
        ui.label('No messages yet').classes('mx-auto my-36')
    ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')

async def initialize_agent():
    global agent
    # Create a new agent
    agent = Agent()
    
    # Configure the agent
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['agent']['custom_system_prompt'] = '你会用萌萌哒的语气回复'
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['deepseek']['model'] = 'deepseek-chat'
    config['qwen']['api_key'] = os.getenv('QWEN_API_KEY')
    config['qwen']['base_url'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    config['agent']['max_iterations'] = 100
    
    # Set configuration
    agent.set_config(config)
    
    # Add tools to the agent
    agent.add_tool("./tools/forecast.py")
    
    # Initialize the agent
    print("Initializing agent...")
    await agent.initialize()
    print("Agent initialized successfully!")

@ui.page('/')
async def main():
    global agent
    
    user_id = str(uuid4())
    bot_id = "agent"
    user_avatar = f'https://robohash.org/{user_id}?bgset=bg2'
    bot_avatar = f'https://robohash.org/{bot_id}?bgset=bg1'
    
    # Initialize agent if not already done
    if agent is None:
        with ui.dialog() as dialog, ui.card():
            ui.label('Initializing FractFlow Agent...')
            ui.spinner(size='lg')
        dialog.open()
        await initialize_agent()
        dialog.close()

    # Add a loading indicator that can be shown/hidden
    loading_indicator = ui.spinner(size='lg').classes('absolute bottom-4 right-4')
    loading_indicator.visible = False
    
    async def send() -> None:
        if not text.value.strip():
            return
            
        user_message = text.value
        stamp = datetime.now().strftime('%X')
        
        # Add user message to chat
        messages.append((user_id, user_avatar, user_message, stamp))
        text.value = ''
        chat_messages.refresh()
        
        # Show loading indicator
        loading_indicator.visible = True
        
        try:
            # Process query with agent
            result = await agent.process_query(user_message)
            
            # Add agent response to chat
            agent_stamp = datetime.now().strftime('%X')
            messages.append((bot_id, bot_avatar, result, agent_stamp))
            chat_messages.refresh()
        except Exception as e:
            # Handle errors
            error_message = f"Error: {str(e)}"
            messages.append((bot_id, bot_avatar, error_message, datetime.now().strftime('%X')))
            chat_messages.refresh()
        finally:
            # Hide loading indicator
            loading_indicator.visible = False

    ui.add_css(r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}')
    
    with ui.header().classes('bg-primary text-white'):
        ui.label('FractFlow Agent Chat').classes('text-h5 q-px-md q-py-sm')
    
    with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
        with ui.row().classes('w-full no-wrap items-center'):
            with ui.avatar():
                ui.image(user_avatar)
            text = ui.input(placeholder='Ask the FractFlow Agent...').on('keydown.enter', send) \
                .props('rounded outlined input-class=mx-3').classes('flex-grow')
            ui.button('Send', on_click=send).props('icon=send')
        ui.markdown('Built with [FractFlow](https://github.com/yourusername/FractFlow) and [NiceGUI](https://nicegui.io)') \
            .classes('text-xs self-end mr-8 m-[-1em] text-primary')

    await ui.context.client.connected()
    with ui.column().classes('w-full max-w-2xl mx-auto items-stretch'):
        chat_messages(user_id)

@ui.page('/shutdown')
async def shutdown_page():
    global agent
    
    if agent:
        ui.label('Shutting down agent...')
        await agent.shutdown()
        agent = None
        ui.label('Agent has been shut down.')
    else:
        ui.label('Agent is not running.')
        
    ui.button('Return to Chat', on_click=lambda: ui.navigate.to('/')).classes('mt-4')

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title="FractFlow Agent Chat") 