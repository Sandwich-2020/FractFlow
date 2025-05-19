# Tool Generator (toolgen)

一个用于快速生成FractFlow工具模板的工具，帮助用户专注于功能实现而不是模板代码。

## 功能特点

- 自动生成完整的工具项目结构
- 创建所有必要的模板文件
- 用户只需要实现核心功能代码
- 模板包含详细的注释和TODOs，指导用户正确实现
- 提供完整的单元测试和集成测试模板

## 安装

确保您已安装jinja2：

```bash
pip install jinja2
```

## 使用方法

### 命令行方式

```bash
# 基本用法
python -m tools.toolgen.cli target_path --name "Tool Name" --description "Tool description"

# 示例
python -m tools.toolgen.cli tools/my_new_tool --name "Weather Forecast" --description "A tool for retrieving weather forecasts"
```

### 在代码中使用

```python
from tools.toolgen import generate_tool

generate_tool(
    target_path="tools/my_new_tool",
    tool_name="Weather Forecast",
    description="A tool for retrieving weather forecasts"
)
```

## 生成的项目结构

```
target_path/
│
├── src/
│   ├── __init__.py
│   ├── AI_server.py
│   ├── server.py
│   └── tool_name_operations.py  # 用户需要实现的文件
│
├── tests/
│   ├── __init__.py
│   ├── test_tool_name_unit.py      # 单元测试
│   └── test_tool_name_integration.py  # 集成测试
│
├── docs/
│   └── User-Intention.md
│
├── run_server.py
└── requirements.txt
```

## 测试功能

工具生成器提供两种类型的测试模板：

1. **单元测试**：针对核心功能代码的测试，直接测试operations文件中的函数
2. **集成测试**：通过subprocess调用run_server.py，测试整个系统在实际环境中的表现

### 运行测试

```bash
# 运行单元测试
cd target_path
python -m unittest tests/test_tool_name_unit.py

# 运行集成测试
python -m unittest tests/test_tool_name_integration.py

# 运行所有测试
python -m unittest discover tests
```

## 工作流程

1. 使用toolgen生成工具模板
2. 在`src/tool_name_operations.py`中实现核心功能
3. 在`src/server.py`中修改导入并添加API端点
4. 根据功能需求更新单元测试和集成测试
5. 根据需要自定义`AI_server.py`中的系统提示和配置
6. 运行`run_server.py`启动您的工具

## 注意事项

- 不要修改模板文件的基本结构
- 遵循注释中的TODO指示
- 保持operations文件中的函数签名与server.py中的API一致
- 测试文件可以根据您的具体功能需求扩展

## 贡献

欢迎提交问题报告和改进建议! 