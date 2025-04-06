# EnvisionCore v2

EnvisionCore is a modular agent framework that integrates language models with tools to create powerful AI assistants.

## Project Structure

```
EnvisionCore-v2/
├── src/                          # Main source code
│   ├── core/                     # Core framework components
│   │   ├── orchestrator.py       # High-level orchestration
│   │   ├── query_processor.py    # User query processing
│   │   └── tool_executor.py      # Tool execution logic
│   ├── models/                   # Model implementations
│   │   ├── base_model.py         # Model interface
│   │   ├── deepseek_model.py     # DeepSeek implementation
│   │   ├── factory.py            # Model factory
│   │   └── openai_model.py       # OpenAI implementation (placeholder)
│   ├── conversation/             # Conversation management
│   │   ├── base_history.py       # Conversation history management
│   │   └── provider_adapters/    # Provider-specific conversation adapters
│   ├── tools/                    # Tool implementations
│   │   ├── mcp/                  # MCP integration
│   │   ├── filesystem/           # Filesystem operations
│   │   └── ...                   # Other tool implementations
│   ├── infra/                    # Infrastructure components
│   │   ├── config.py             # Configuration management
│   │   └── error_handling.py     # Error handling utilities
│   └── agent.py                  # Main entry point
├── tests/                        # Test directory
└── docs/                         # Documentation
```

## Getting Started

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env` file:
   ```
   DEEPSEEK_API_KEY=your_deepseek_api_key
   DEEPSEEK_BASE_URL=https://api.deepseek.com
   DEEPSEEK_MODEL_NAME=deepseek-reasoner
   ```

### Running the Agent

```
python src/agent.py --provider deepseek
```

## Features

- Modular architecture separating concerns for easier maintenance and extension
- Provider-neutral interfaces allowing multiple LLM providers 
- Integrated MCP (Model Context Protocol) tools support
- Native support for DeepSeek models (OpenAI to be implemented)
- Configurable via environment variables or configuration files

## Adding New Tools

1. Create a new directory under `src/tools/` for your tool
2. Implement the tool using the MCP protocol
3. Register the tool in `src/agent.py`

## Adding New Model Providers

1. Create a new implementation of `BaseModel` in the `src/models/` directory
2. Update the model factory in `src/models/factory.py` to support the new provider
3. Create a provider-specific adapter in `src/conversation/provider_adapters/` 