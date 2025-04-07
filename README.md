# FractalMCP

FractalMCP is a modular agent framework that integrates language models with tools to create powerful AI assistants.

## Installation

```bash
pip install FractalMCP
```

## Quick Start

```python
import asyncio
from FractalMCP.agent import Agent

async def main():
    # Create a new agent
    agent = Agent()
    
    # Get the current configuration
    config = agent.get_config()
    
    # Update configuration with API keys
    config['deepseek']['api_key'] = 'your_api_key'
    
    # Set the updated configuration
    agent.set_config(config)
    
    # Add tools to the agent
    agent.add_tool("./tools/filesystem/operations.py")
    agent.add_tool("./tools/weather/forecast.py")
    
    # Initialize the agent (starts up the tool servers)
    await agent.initialize()
    
    try:
        # Interactive chat loop
        print("Agent chat started. Type 'exit', 'quit', or 'bye' to end the conversation.")
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ('exit', 'quit', 'bye'):
                break
                
            print("\nAgent: ", end="")
            result = await agent.process_query(user_input)
            print(result)
    finally:
        # Shut down the agent gracefully
        await agent.shutdown()
        print("\nAgent chat ended.")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### Agent Class

The main interface for using FractalMCP.

#### Constructor

```python
agent = Agent(system_prompt=None, provider=None)
```

- `system_prompt`: Optional system prompt to initialize the agent
- `provider`: Optional AI provider to use (e.g., 'openai', 'deepseek', 'qwen')

#### Methods

- `get_config()`: Get the current configuration dictionary
- `set_config(config)`: Set the configuration dictionary
- `add_tool(tool_path, tool_name=None)`: Add a tool to the agent
- `initialize()`: Initialize and start the agent system (async)
- `shutdown()`: Shut down the agent system (async)
- `process_query(query)`: Process a user query and return the agent's response (async)

## Project Structure

```
FractalMCP/
├── core/                     # Core framework components
│   ├── orchestrator.py       # High-level orchestration
│   ├── query_processor.py    # User query processing
│   └── tool_executor.py      # Tool execution logic
├── models/                   # Model implementations
│   ├── base_model.py         # Model interface
│   ├── deepseek_model.py     # DeepSeek implementation
│   ├── factory.py            # Model factory
│   └── openai_model.py       # OpenAI implementation
├── conversation/             # Conversation management
│   ├── base_history.py       # Conversation history management
│   └── provider_adapters/    # Provider-specific conversation adapters
├── mcpcore/                  # MCP integration
├── infra/                    # Infrastructure components
│   ├── config.py             # Configuration management
│   └── error_handling.py     # Error handling utilities
└── agent.py                  # Main user interface
```

## Configuration

FractalMCP can be configured using the `get_config()` and `set_config()` methods. The configuration structure is:

```python
config = {
    'openai': {
        'api_key': 'your_openai_api_key',
        'base_url': 'https://api.openai.com',
        'model': 'gpt-4',
        'tool_calling_model': 'gpt-3.5-turbo'
    },
    'deepseek': {
        'api_key': 'your_deepseek_api_key',
        'base_url': 'https://api.deepseek.com',
        'model': 'deepseek-reasoner',
        'tool_calling_model': 'deepseek-chat'
    },
    'qwen': {
        'api_key': 'your_qwen_api_key',
        'base_url': 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1',
        'model': 'qwen-max',
        'tool_calling_model': 'qwen-turbo'
    },
    'agent': {
        'max_iterations': 10,
        'provider': 'deepseek'
    }
}
```

## Adding New Tools

1. Create a new directory under `tools/` for your tool
2. Implement the tool using the MCP protocol
3. Add the tool to the agent using `agent.add_tool(tool_path)`

## Adding New Model Providers

1. Create a new implementation of `BaseModel` in the `FractalMCP/models/` directory
2. Update the model factory in `FractalMCP/models/factory.py` to support the new provider
3. Create a provider-specific adapter in `FractalMCP/conversation/provider_adapters/` 