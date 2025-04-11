import os
import subprocess
from typing import List, Dict
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import json

mcp = FastMCP("code_executor")

@mcp.tool()
async def spec_parser(user_request: str) -> str:
    """
    Converts natural language requirements into a structured JSON specification for software architecture.
    
    This function calls the DeepSeek Chat API to transform user requirements into a formal specification 
    that includes task description, module breakdown, and function definitions with their parameters,
    return types, and documentation.
    
    Args:
        user_request (str): Natural language description of the software requirements or features
                            the user wants to implement.
        
    Returns:
        str: A JSON-formatted string containing the structured specification with the following structure:
             {
                "task_brief": "Brief description of the overall task",
                "modules": [
                    {
                        "name": "Module name",
                        "description": "Module responsibility description",
                        "functions": [
                            {
                                "name": "function_name",
                                "params": {"param1": "type1", ...},
                                "returns": "return_type",
                                "doc": "Function documentation"
                            },
                            ...
                        ]
                    },
                    ...
                ]
             }
             
    Example:
        >>> spec = await spec_parser("Create a task management system with the ability to add, delete, and mark tasks as complete")
        >>> # Returns a JSON string with modules like TaskManager, Task, etc.
        
    Note:
        Requires a valid DeepSeek API key to function correctly.
    """
    client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key='sk-fd20bf9c2c0f4c9ea49ae5ed53037504',
    base_url="https://api.deepseek.com",)
    model_name = "deepseek-chat"
    SYSTEM_PROMPT = """
    你是一个经验丰富的软件架构师，善于将自然语言的需求转化为结构化的模块设计。
    请根据以下用户需求，输出包含任务说明、模块划分、每个模块的职责、关键函数的名称、参数、返回类型和说明。

    用户需求：
    "{user_request}"

    请用 JSON 格式输出，如下：
    {{
    "task_brief": "...",
    "modules": [
        {{
        "name": "...",
        "description": "...",
        "functions": [
            {{
            "name": "...",
            "params": {{"param1": "type1", ...}},
            "returns": "...",
            "doc": "..."
            }},
            ...
        ]
        }},
        ...
    ]
    }}
    """
    completion = client.chat.completions.create(
        model=model_name, 
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_request}
            ]
    )
    
    # Return the completion content
    return completion.choices[0].message.content


@mcp.tool()
async def code_writer(module_name: str, functions: List[Dict]) -> str:
    """
    根据结构化函数设计信息，生成完整的 Python 模块代码。
    
    Args:
        module_name: 模块名（文件名用）
        functions: 一个函数草图列表，每个字典含 name, params, returns, doc
    
    Returns:
        str: Python 模块源码
    """
    client = OpenAI(
        api_key="sk-fd20bf9c2c0f4c9ea49ae5ed53037504",
        base_url="https://api.deepseek.com",
    )

    model = "deepseek-chat"
    all_code = []

    PROMPT_TEMPLATE = """
    你是一位经验丰富的 Python 工程师。请根据以下函数设计信息，编写完整的 Python 函数（包括函数定义与 docstring），风格清晰、易读。

    模块名：{module_name}

    函数名：{name}
    参数：{params}
    返回值类型：{returns}
    函数功能描述：{doc}

    请输出完整函数代码，包含 docstring。
    """

    def make_prompt(module_name: str, func: Dict) -> str:
        return PROMPT_TEMPLATE.format(
            module_name=module_name,
            name=func.get("name"),
            params=json.dumps(func.get("params", {}), ensure_ascii=False),
            returns=func.get("returns", "Any"),
            doc=func.get("doc", "")
        )
    
    for func in functions:
        prompt = make_prompt(module_name, func)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个代码生成器"},
                {"role": "user", "content": prompt}
            ]
        )
        code = completion.choices[0].message.content.strip()
        all_code.append(code)

    return "\n\n".join(all_code)

@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """
    Writes content to a file at the specified path.
    
    Args:
        path (str): The file path where the content will be written. If the file already exists, 
                   it will be overwritten.
        content (str): The text content to write to the file.
        
    Returns:
        str: A confirmation message indicating the file has been written.
        
    Example:
        write_file("example.txt", "Hello World!")
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written to {path}"

@mcp.tool()
async def read_file(path: str) -> str:
    """
    Reads and returns the content of a file at the specified path.
    
    Args:
        path (str): The path of the file to read.
        
    Returns:
        str: The content of the file as a string or an error message if the file doesn't exist.
        
    Example:
        read_file("example.txt")
    """
    if not os.path.exists(path):
        return "File does not exist"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@mcp.tool()
async def run_file(path: str) -> str:
    """
    Executes a Python file and returns its output.
    
    Args:
        path (str): The path to the Python file to execute.
        
    Returns:
        str: The combined stdout and stderr output from the execution, or an error message if
             the file doesn't exist or execution times out after 10 seconds.
        
    Example:
        run_file("script.py")
    """
    if not os.path.exists(path):
        return "File does not exist"
    try:
        result = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=10
        )
        return f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Execution timed out"

@mcp.tool()
async def make_dir(path: str, exist_ok: bool = True) -> str:
    """
    Creates a directory at the specified path.
    
    Args:
        path (str): The path where the directory will be created.
        exist_ok (bool, optional): If True, don't raise an error if the directory already exists.
                                  Defaults to True.
        
    Returns:
        str: A confirmation message indicating the directory has been created or a message
             indicating it already exists.
        
    Example:
        make_dir("./projects/new_project")
    """
    try:
        os.makedirs(path, exist_ok=exist_ok)
        return f"Directory created at {path}"
    except FileExistsError:
        return f"Directory already exists at {path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

# @mcp.tool()
# async def delete_file(path: str) -> str:
#     """
#     Deletes a file at the specified path.
#     
#     Args:
#         path (str): The path of the file to delete.
#         
#     Returns:
#         str: A confirmation message indicating the file has been deleted or an error message
#              if the file doesn't exist.
#         
#     Example:
#         delete_file("example.txt")
#     """
#     if os.path.exists(path):
#         os.remove(path)
#         return f"Deleted {path}"
#     else:
#         return "File does not exist"

@mcp.tool()
async def list_dir(path: str) -> list[str]:
    """
    Lists the contents of a directory.
    
    Args:
        path (str): The path of the directory to list.
        
    Returns:
        list[str]: A list of filenames and directory names contained in the specified directory.
                  Returns an empty list if the path is not a directory.
        
    Example:
        list_dir("./projects")
    """
    if not os.path.isdir(path):
        return []
    return os.listdir(path)

@mcp.tool()
async def diff_files(path1: str, path2: str) -> str:
    """
    Compares two files and returns a unified diff of their contents.
    
    Args:
        path1 (str): The path to the first file for comparison.
        path2 (str): The path to the second file for comparison.
        
    Returns:
        str: A unified diff showing the differences between the two files, or an error message
             if one or both files don't exist.
        
    Example:
        diff_files("file1.txt", "file2.txt")
    """
    if not os.path.exists(path1) or not os.path.exists(path2):
        return "One or both files do not exist"
    with open(path1, "r", encoding="utf-8") as f1, open(path2, "r", encoding="utf-8") as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()
    import difflib
    diff = difflib.unified_diff(lines1, lines2, fromfile=path1, tofile=path2)
    return ''.join(diff)

if __name__ == "__main__":
    mcp.run(transport="stdio")
