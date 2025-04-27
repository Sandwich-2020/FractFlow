import os
import sys
import pytest
import tempfile
import shutil
import subprocess
import json
import time
from pathlib import Path
import re

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)


@pytest.fixture
def temp_test_dir():
    """创建临时测试目录并在测试后清理"""
    temp_dir = tempfile.mkdtemp()
    
    # 创建一些测试文件
    test_file = os.path.join(temp_dir, "test_file.txt")
    with open(test_file, "w") as f:
        f.write("This is test content for integration tests")
    
    # 创建一个子目录
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir)
    with open(os.path.join(subdir, "subfile.txt"), "w") as f:
        f.write("This is a file in a subdirectory")
    
    yield temp_dir
    
    # 清理
    shutil.rmtree(temp_dir)


def run_query(query):
    """
    运行单个查询并返回结果
    
    Args:
        query: 要发送到run_server.py的查询字符串
        
    Returns:
        str: 命令输出
    """
    # 确定run_server.py的路径
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run_server.py")
    
    # 使用subprocess执行命令
    process = subprocess.Popen(
        [sys.executable, script_path, "--user_query", query],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        universal_newlines=True
    )
    
    # 捕获输出
    stdout, stderr = process.communicate(timeout=60)
    
    # 检查错误
    if process.returncode != 0:
        print(f"Error executing command: {stderr}")
    
    # 提取结果（去除thinking和其他非结果输出）
    result_match = re.search(r"Result:\s+(.*?)(?:\n\nAgent session ended\.)?$", stdout, re.DOTALL)
    if result_match:
        return result_match.group(1).strip()
    
    return stdout


def test_read_file_query(temp_test_dir):
    """测试读取文件的查询"""
    test_file = os.path.join(temp_test_dir, "test_file.txt")
    
    # 运行查询
    query = f"Read the file {test_file} and tell me its content"
    result = run_query(query)
    
    # 验证结果中含有文件内容
    assert "test content for integration tests" in result


def test_write_file_query(temp_test_dir):
    """测试写入文件的查询"""
    new_file = os.path.join(temp_test_dir, "new_file.txt")
    content = "This is new content created during integration testing"
    
    # 运行查询
    query = f"Create a new file at {new_file} with this content: '{content}'"
    result = run_query(query)
    
    # 验证文件已创建
    assert os.path.exists(new_file)
    
    # 验证内容正确
    with open(new_file, "r") as f:
        file_content = f.read()
    assert content in file_content


def test_list_directory_query(temp_test_dir):
    """测试列出目录内容的查询"""
    # 运行查询
    query = f"List all files and directories in {temp_test_dir}"
    result = run_query(query)
    
    # 验证结果包含已知文件
    assert "test_file.txt" in result
    assert "subdir" in result


def test_file_info_query(temp_test_dir):
    """测试获取文件信息的查询"""
    test_file = os.path.join(temp_test_dir, "test_file.txt")
    
    # 运行查询 - 只请求特定字段
    query = f"Get information about {test_file}, only return the name, size and extension"
    result = run_query(query)
    
    # 验证结果包含请求的信息
    assert "test_file.txt" in result
    assert "size" in result.lower()
    assert ".txt" in result.lower()


def test_copy_file_query(temp_test_dir):
    """测试复制文件的查询"""
    source_file = os.path.join(temp_test_dir, "test_file.txt")
    dest_file = os.path.join(temp_test_dir, "copied_file.txt")
    
    # 运行查询
    query = f"Copy the file from {source_file} to {dest_file}"
    result = run_query(query)
    
    # 验证文件已复制
    assert os.path.exists(dest_file)
    
    # 验证内容匹配
    with open(source_file, "r") as src, open(dest_file, "r") as dst:
        assert src.read() == dst.read()


def test_move_file_query(temp_test_dir):
    """测试移动文件的查询"""
    # 先创建一个要移动的文件
    source_file = os.path.join(temp_test_dir, "to_move.txt")
    with open(source_file, "w") as f:
        f.write("This file will be moved")
    
    dest_file = os.path.join(temp_test_dir, "moved_file.txt")
    
    # 运行查询
    query = f"Move the file {source_file} to {dest_file}"
    result = run_query(query)
    
    # 验证文件已移动
    assert not os.path.exists(source_file)
    assert os.path.exists(dest_file)


def test_delete_file_query(temp_test_dir):
    """测试删除文件的查询"""
    # 创建一个要删除的文件
    file_to_delete = os.path.join(temp_test_dir, "to_delete.txt")
    with open(file_to_delete, "w") as f:
        f.write("This file will be deleted")
    
    # 验证文件存在
    assert os.path.exists(file_to_delete)
    
    # 运行查询
    query = f"Delete the file at {file_to_delete}"
    result = run_query(query)
    
    # 验证文件已删除
    assert not os.path.exists(file_to_delete)


def test_exists_query(temp_test_dir):
    """测试检查文件是否存在的查询"""
    existing_file = os.path.join(temp_test_dir, "test_file.txt")
    nonexistent_file = os.path.join(temp_test_dir, "does_not_exist.txt")
    
    # 运行查询 - 存在的文件
    query = f"Check if the file {existing_file} exists"
    result = run_query(query)
    
    # 验证结果表明文件存在
    assert "exists" in result.lower() or "true" in result.lower()
    
    # 运行查询 - 不存在的文件
    query = f"Check if the file {nonexistent_file} exists"
    result = run_query(query)
    
    # 验证结果表明文件不存在
    assert "not" in result.lower() or "false" in result.lower()


def test_complex_query(temp_test_dir):
    """测试复杂的多步骤查询"""
    # 创建一个子目录用于移动文件
    new_dir = os.path.join(temp_test_dir, "new_directory")
    source_file = os.path.join(temp_test_dir, "test_file.txt")
    dest_file = os.path.join(new_dir, "moved_test_file.txt")
    
    # 运行查询 - 创建目录
    query1 = f"Create a directory at {new_dir}"
    run_query(query1)
    
    # 验证目录已创建
    assert os.path.exists(new_dir)
    assert os.path.isdir(new_dir)
    
    # 运行查询 - 移动文件到新目录
    query2 = f"Move the file {source_file} to {dest_file}"
    run_query(query2)
    
    # 验证文件已移动
    assert not os.path.exists(source_file)
    assert os.path.exists(dest_file)
    
    # 运行查询 - 列出新目录内容
    query3 = f"List all files in {new_dir}"
    result = run_query(query3)
    
    # 验证结果显示移动的文件
    assert "moved_test_file.txt" in result


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 