"""
Code Generation Tool Tests

This module contains tests for the Code Generation Tool (codegen2).
It tests the core functionality of reading and editing files.

Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-08-11
License: MIT License
"""

import unittest
import os
import sys
import asyncio
from pathlib import Path
import tempfile

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

import src.file_io as file_io

class TestCodeGen2(unittest.TestCase):
    """Test cases for the codegen2 module."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        
        # Create a test file
        with open(self.test_file_path, "w") as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

    def tearDown(self):
        """Clean up the test environment."""
        # Remove the temporary directory
        self.temp_dir.cleanup()
        
    def run_async(self, coro):
        """Helper method to run async functions in tests."""
        return asyncio.run(coro)

    def test_read_file(self):
        """Test the read_file function."""
        # Read file without line numbers
        content = self.run_async(file_io.read_file(self.test_file_path, False))
        self.assertEqual(content, "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        
        # Read file with line numbers
        content_with_numbers = self.run_async(file_io.read_file(self.test_file_path, True))
        expected_content = "1|Line 1\n2|Line 2\n3|Line 3\n4|Line 4\n5|Line 5"
        self.assertEqual(content_with_numbers, expected_content)

    def test_read_file_with_line_range(self):
        """Test the read_file_with_line_range function."""
        # Read lines 2-4
        content, start, end = self.run_async(file_io.read_file_with_line_range(self.test_file_path, 2, 4))
        self.assertEqual(content, "Line 2\nLine 3\nLine 4\n")
        self.assertEqual(start, 2)
        self.assertEqual(end, 4)
        
        # Read from line 3 to end
        content, start, end = self.run_async(file_io.read_file_with_line_range(self.test_file_path, 3))
        self.assertEqual(content, "Line 3\nLine 4\nLine 5\n")
        self.assertEqual(start, 3)
        self.assertEqual(end, 5)

    def test_list_directory(self):
        """Test the list_directory function."""
        # Create some files and directories for testing
        os.makedirs(os.path.join(self.temp_dir.name, "subdir"))
        with open(os.path.join(self.temp_dir.name, "file1.txt"), "w") as f:
            f.write("File 1 content")
        with open(os.path.join(self.temp_dir.name, "file2.txt"), "w") as f:
            f.write("File 2 content")
            
        # List the directory
        result = self.run_async(file_io.list_directory(self.temp_dir.name))
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)  # 1 subdir, 2 files created here, 1 test_file.txt from setUp
        
        # Verify at least one directory and one file
        has_dir = any(item["is_dir"] for item in result)
        has_file = any(not item["is_dir"] for item in result)
        self.assertTrue(has_dir)
        self.assertTrue(has_file)
        
        # Verify item structure
        for item in result:
            self.assertIn("name", item)
            self.assertIn("path", item)
            self.assertIn("is_dir", item)
            self.assertIn("type", item)
            self.assertIn("size", item)
            self.assertIn("modified", item)

    def test_edit_file_replace(self):
        """Test replacing content in a file."""
        # Replace lines 2-4
        success = self.run_async(file_io.edit_file(self.test_file_path, "New Line 2\nNew Line 3\nNew Line 4\n", 2, 4))
        self.assertTrue(success)
        
        # Read the file to verify
        content = self.run_async(file_io.read_file(self.test_file_path, False))
        self.assertEqual(content, "Line 1\nNew Line 2\nNew Line 3\nNew Line 4\nLine 5\n")

    def test_edit_file_append(self):
        """Test appending content to a file."""
        # Append a line
        success = self.run_async(file_io.edit_file(self.test_file_path, "Line 6\n", -1))
        self.assertTrue(success)
        
        # Read the file to verify
        content = self.run_async(file_io.read_file(self.test_file_path, False))
        self.assertEqual(content, "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\n")

    def test_edit_file_create(self):
        """Test creating a new file."""
        # Create a new file
        new_file_path = os.path.join(self.temp_dir.name, "new_file.txt")
        success = self.run_async(file_io.edit_file(new_file_path, "New file content\n"))
        self.assertTrue(success)
        
        # Check that the file exists
        self.assertTrue(os.path.exists(new_file_path))
        
        # Read the file to verify
        content = self.run_async(file_io.read_file(new_file_path, False))
        self.assertEqual(content, "New file content\n")

    def test_remove_lines(self):
        """Test removing lines from a file."""
        # Remove lines 2-4
        success = self.run_async(file_io.remove_lines(self.test_file_path, 2, 4))
        self.assertTrue(success)
        
        # Read the file to verify
        content = self.run_async(file_io.read_file(self.test_file_path, False))
        self.assertEqual(content, "Line 1\nLine 5\n")
        
        # Test removing from a line to the end
        # First, restore the file
        with open(self.test_file_path, "w") as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        
        # Remove from line 3 to the end
        success = self.run_async(file_io.remove_lines(self.test_file_path, 3))
        self.assertTrue(success)
        
        # Read the file to verify
        content = self.run_async(file_io.read_file(self.test_file_path, False))
        self.assertEqual(content, "Line 1\nLine 2\n")


if __name__ == "__main__":
    unittest.main() 