#!/usr/bin/env python3
"""
ui.py
Description: UI implementation for FractFlow using NiceGUI
"""

import asyncio
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from nicegui import ui

from FractFlow.agent import Agent


class FractFlowUI:
    """UI implementation for FractFlow using NiceGUI"""
    
    def __init__(self, agent: Agent):
        """Initialize the UI with an agent instance"""
        self.agent = agent
        self.messages: List[Tuple[str, str, str, str]] = []
        self.user_id = str(uuid4())
        self.bot_id = "agent"
        self._is_initialized = False
        self._loading_indicator = None
        
        # Setup UI page
        @ui.page('/')
        async def main():
            await self._setup_ui()

    async def initialize(self):
        """Initialize the agent"""
        if not self._is_initialized:
            await self.agent.initialize()
            self._is_initialized = True

    async def _setup_ui(self):
        """Setup the UI components"""
        # Setup header
        with ui.header().classes('bg-primary text-white'):
            ui.label('FractFlow Chat').classes('text-h5 q-px-md q-py-sm')
        
        # Setup chat area
        with ui.column().classes('w-full max-w-2xl mx-auto items-stretch'):
            self._setup_chat_messages()
        
        # Setup input area
        with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
            self._setup_input_area()
            
        # Setup loading indicator
        self._loading_indicator = ui.spinner(size='lg').classes('absolute bottom-4 right-4')
        self._loading_indicator.visible = False

    @ui.refreshable
    def _chat_messages(self):
        """Display chat messages"""
        if self.messages:
            for user_id, avatar, text, stamp in self.messages:
                ui.chat_message(
                    text=text,
                    stamp=stamp,
                    avatar=avatar,
                    sent=user_id == self.user_id
                )
        else:
            ui.label('No messages yet').classes('mx-auto my-36')
        ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')

    def _setup_chat_messages(self):
        """Setup the chat messages display"""
        self._chat_messages()

    def _setup_input_area(self):
        """Setup the input area"""
        with ui.row().classes('w-full no-wrap items-center'):
            with ui.avatar():
                ui.image(f'https://robohash.org/{self.user_id}?bgset=bg2')
            text = ui.input(placeholder='Ask the FractFlow Agent...') \
                .on('keydown.enter', lambda: asyncio.create_task(self._handle_message(text.value))) \
                .props('rounded outlined input-class=mx-3').classes('flex-grow')
            ui.button('Send', on_click=lambda: asyncio.create_task(self._handle_message(text.value))) \
                .props('icon=send')
        
        ui.markdown('Built with [FractFlow](https://github.com/yourusername/FractFlow) and [NiceGUI](https://nicegui.io)') \
            .classes('text-xs self-end mr-8 m-[-1em] text-primary')

    async def _handle_message(self, text: str):
        """Handle user message"""
        if not text.strip():
            return
            
        # Add user message
        self._add_user_message(text)
        
        # Show loading indicator
        self._loading_indicator.visible = True
        
        try:
            # Process with agent
            result = await self.agent.process_query(text)
            self._add_bot_message(result)
        except Exception as e:
            self._add_error_message(str(e))
        finally:
            # Hide loading indicator
            self._loading_indicator.visible = False

    def _add_user_message(self, text: str):
        """Add a user message"""
        self.messages.append((
            self.user_id,
            f'https://robohash.org/{self.user_id}?bgset=bg2',
            text,
            datetime.now().strftime('%X')
        ))
        self._chat_messages.refresh()

    def _add_bot_message(self, text: str):
        """Add a bot message"""
        self.messages.append((
            self.bot_id,
            f'https://robohash.org/{self.bot_id}?bgset=bg1',
            text,
            datetime.now().strftime('%X')
        ))
        self._chat_messages.refresh()

    def _add_error_message(self, error: str):
        """Add an error message"""
        self.messages.append((
            self.bot_id,
            f'https://robohash.org/{self.bot_id}?bgset=bg1',
            f"Error: {error}",
            datetime.now().strftime('%X')
        ))
        self._chat_messages.refresh()

    async def shutdown(self):
        """Shutdown the UI and agent"""
        if self._is_initialized:
            await self.agent.shutdown()
            self._is_initialized = False

    @staticmethod
    def run():
        """Run the UI server"""
        ui.run(title="FractFlow Chat") 