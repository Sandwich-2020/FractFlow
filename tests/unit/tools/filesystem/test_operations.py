"""
文件系统操作模块的单元测试。
"""

import os
import tempfile
import pytest
import shutil
from unittest import mock
from typing import Dict, Any, List

from src.tools.filesystem.operations import (
    list_directory_contents,
    create_file,
    delete_file,
    copy_file,
    move_file,
    format_size
)

class TestFilesystemOperations:
    """文件系统操作函数测试。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 清理
        shutil.rmtree(temp_dir)
    
    def test_list_directory_contents(self, temp_dir):
        """测试列出目录内容。"""
        # 创建测试文件和目录
        os.mkdir(os.path.join(temp_dir, "test_dir"))
        with open(os.path.join(temp_dir, "test_file.txt"), "w") as f:
            f.write("test content")
        
        # 列出目录内容
        result = list_directory_contents(temp_dir)
        
        # 验证结果
        assert isinstance(result, dict)
        assert "directories" in result
        assert "files" in result
        assert "test_dir" in result["directories"]
        assert "test_file.txt" in result["files"]
    
    def test_create_file(self, temp_dir):
        """测试创建文件。"""
        test_file = os.path.join(temp_dir, "created_file.txt")
        test_content = "This is test content."
        
        # 创建文件
        result = create_file(test_file, test_content)
        
        # 验证结果
        assert result["success"] is True
        assert os.path.exists(test_file)
        with open(test_file, "r") as f:
            assert f.read() == test_content
    
    def test_create_file_failure(self, temp_dir):
        """测试创建文件失败情况。"""
        # 创建不可写目录
        readonly_dir = os.path.join(temp_dir, "readonly")
        os.mkdir(readonly_dir)
        test_file = os.path.join(readonly_dir, "test.txt")
        
        # 模拟写入失败
        with mock.patch("builtins.open", mock.mock_open()) as mock_file:
            mock_file.side_effect = PermissionError("Permission denied")
            result = create_file(test_file, "content")
        
        # 验证结果
        assert result["success"] is False
        assert "error" in result
        assert "Permission denied" in result["error"]
    
    def test_delete_file(self, temp_dir):
        """测试删除文件。"""
        # 创建测试文件
        test_file = os.path.join(temp_dir, "to_delete.txt")
        with open(test_file, "w") as f:
            f.write("content to delete")
        
        # 删除文件
        result = delete_file(test_file)
        
        # 验证结果
        assert result["success"] is True
        assert not os.path.exists(test_file)
    
    def test_delete_file_nonexistent(self, temp_dir):
        """测试删除不存在的文件。"""
        nonexistent_file = os.path.join(temp_dir, "nonexistent.txt")
        
        # 删除不存在的文件
        result = delete_file(nonexistent_file)
        
        # 验证结果
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_copy_file(self, temp_dir):
        """测试复制文件。"""
        # 创建源文件
        source_file = os.path.join(temp_dir, "source.txt")
        with open(source_file, "w") as f:
            f.write("source content")
        
        # 目标文件路径
        target_file = os.path.join(temp_dir, "target.txt")
        
        # 复制文件
        result = copy_file(source_file, target_file)
        
        # 验证结果
        assert result["success"] is True
        assert os.path.exists(target_file)
        with open(target_file, "r") as f:
            assert f.read() == "source content"
    
    def test_copy_file_source_missing(self, temp_dir):
        """测试复制不存在的源文件。"""
        source_file = os.path.join(temp_dir, "missing.txt")
        target_file = os.path.join(temp_dir, "target.txt")
        
        # 复制不存在的文件
        result = copy_file(source_file, target_file)
        
        # 验证结果
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_move_file(self, temp_dir):
        """测试移动文件。"""
        # 创建源文件
        source_file = os.path.join(temp_dir, "to_move.txt")
        with open(source_file, "w") as f:
            f.write("move content")
        
        # 目标文件路径
        target_file = os.path.join(temp_dir, "moved.txt")
        
        # 移动文件
        result = move_file(source_file, target_file)
        
        # 验证结果
        assert result["success"] is True
        assert not os.path.exists(source_file)
        assert os.path.exists(target_file)
        with open(target_file, "r") as f:
            assert f.read() == "move content"
    
    def test_move_file_source_missing(self, temp_dir):
        """测试移动不存在的源文件。"""
        source_file = os.path.join(temp_dir, "nonexistent.txt")
        target_file = os.path.join(temp_dir, "target.txt")
        
        # 移动不存在的文件
        result = move_file(source_file, target_file)
        
        # 验证结果
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_format_size(self):
        """测试格式化文件大小。"""
        assert format_size(0) == "0 B"
        assert format_size(1000) == "1000 B"
        assert format_size(1024) == "1.0 KB"
        assert format_size(1024 * 1024) == "1.0 MB"
        assert format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_size(1234567890) == "1.1 GB"
