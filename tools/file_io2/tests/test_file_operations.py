import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to sys.path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.file_operations import (
    check_file_exists,
    get_file_line_count,
    read_file_range,
    read_file_chunks,
    read_file_with_line_numbers,
    create_or_write_file,
    append_to_file,
    insert_at_line,
    delete_line
)


class TestFileOperations(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create test files with known content
        self.empty_file_path = os.path.join(self.test_dir, "empty_file.txt")
        Path(self.empty_file_path).touch()
        
        self.small_file_path = os.path.join(self.test_dir, "small_file.txt")
        with open(self.small_file_path, 'w', encoding='utf-8') as f:
            f.write("Line 1\nLine 2\nLine 3\n")
            
        self.medium_file_path = os.path.join(self.test_dir, "medium_file.txt")
        with open(self.medium_file_path, 'w', encoding='utf-8') as f:
            for i in range(1, 21):
                f.write(f"This is line {i}\n")
        
        # Path to a file that doesn't exist
        self.nonexistent_file_path = os.path.join(self.test_dir, "nonexistent.txt")
        
        # Path to a nested file that doesn't exist yet
        self.nested_file_path = os.path.join(self.test_dir, "nested", "dir", "test.txt")
    
    def tearDown(self):
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_check_file_exists(self):
        # Test existing file
        result = check_file_exists(self.small_file_path)
        self.assertTrue(result["exists"])
        self.assertEqual(result["path"], os.path.abspath(self.small_file_path))
        
        # Test non-existent file
        result = check_file_exists(self.nonexistent_file_path)
        self.assertFalse(result["exists"])
        self.assertIn("message", result)
    
    def test_get_file_line_count(self):
        # Test empty file
        result = get_file_line_count(self.empty_file_path)
        self.assertTrue(result["success"])
        self.assertEqual(result["line_count"], 0)
        
        # Test small file
        result = get_file_line_count(self.small_file_path)
        self.assertTrue(result["success"])
        self.assertEqual(result["line_count"], 3)
        
        # Test medium file
        result = get_file_line_count(self.medium_file_path)
        self.assertTrue(result["success"])
        self.assertEqual(result["line_count"], 20)
        
        # Test non-existent file
        result = get_file_line_count(self.nonexistent_file_path)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "File not found")
    
    def test_read_file_range(self):
        # Test reading entire small file
        result = read_file_range(self.small_file_path)
        self.assertTrue(result["success"])
        self.assertEqual(result["content"], "Line 1\nLine 2\nLine 3\n")
        self.assertEqual(result["start_line"], 1)
        self.assertEqual(result["end_line"], 3)
        
        # Test reading a range from medium file
        result = read_file_range(self.medium_file_path, 5, 10)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["lines"]), 6)  # Lines 5-10 inclusive
        self.assertEqual(result["start_line"], 5)
        self.assertEqual(result["end_line"], 10)
        
        # Test invalid start line
        result = read_file_range(self.small_file_path, 0)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid start line")
        
        # Test start line beyond file length
        result = read_file_range(self.small_file_path, 10)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid start line")
        
        # Test non-existent file
        result = read_file_range(self.nonexistent_file_path)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "File not found")
        
        # Test empty file
        result = read_file_range(self.empty_file_path)
        self.assertTrue(result["success"])
        self.assertEqual(result["content"], "")
        self.assertEqual(result["line_count"], 0)
    
    def test_read_file_chunks(self):
        # Test getting chunk metadata for medium file
        result = read_file_chunks(self.medium_file_path, 5)
        self.assertTrue(result["success"])
        # For a 20-line file with chunk size 5, we expect 5 chunks
        # (due to our formula in read_file_chunks)
        self.assertEqual(result["chunk_count"], 5)
        self.assertEqual(len(result["chunks"]), 5)
        
        # Test getting a specific chunk
        result = read_file_chunks(self.medium_file_path, 5, chunk_index=1)
        self.assertTrue(result["success"])
        self.assertEqual(result["chunk_index"], 1)
        self.assertEqual(result["start_line"], 6)
        self.assertEqual(result["end_line"], 10)
        
        # Test with overlap
        result = read_file_chunks(self.medium_file_path, 6, overlap=2)
        self.assertTrue(result["success"])
        chunks = result["chunks"]
        # Check that chunks overlap correctly
        self.assertEqual(chunks[0]["end_line"], 6)
        self.assertEqual(chunks[1]["start_line"], 5)  # Overlap of 2 lines
        
        # Test invalid chunk size
        result = read_file_chunks(self.medium_file_path, 0)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid chunk size")
        
        # Test invalid overlap
        result = read_file_chunks(self.medium_file_path, 5, overlap=5)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid overlap")
        
        # Test invalid chunk index
        result = read_file_chunks(self.medium_file_path, 5, chunk_index=10)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid chunk index")
    
    def test_read_file_with_line_numbers(self):
        # Test reading with line numbers
        result = read_file_with_line_numbers(self.small_file_path)
        self.assertTrue(result["success"])
        
        # Check that line numbers are included in content
        content_lines = result["content"].strip().split('\n')
        self.assertEqual(len(content_lines), 3)
        self.assertIn("1 |", content_lines[0])
        self.assertIn("2 |", content_lines[1])
        self.assertIn("3 |", content_lines[2])
        
        # Test reading a range with line numbers
        result = read_file_with_line_numbers(self.medium_file_path, 5, 7)
        self.assertTrue(result["success"])
        content_lines = result["content"].strip().split('\n')
        self.assertEqual(len(content_lines), 3)
        self.assertIn("5 |", content_lines[0])
        self.assertIn("6 |", content_lines[1])
        self.assertIn("7 |", content_lines[2])
    
    def test_create_or_write_file(self):
        # Test creating a new file
        test_content = "This is a test file.\nWith multiple lines.\n"
        result = create_or_write_file(self.nonexistent_file_path, test_content)
        self.assertTrue(result["success"])
        
        # Verify the file was created with correct content
        with open(self.nonexistent_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, test_content)
        
        # Test overwriting an existing file
        new_content = "This file has been overwritten."
        result = create_or_write_file(self.nonexistent_file_path, new_content)
        self.assertTrue(result["success"])
        
        # Verify the file was overwritten
        with open(self.nonexistent_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, new_content)
        
        # Test creating a file in a nested directory that doesn't exist
        result = create_or_write_file(self.nested_file_path, "Nested file content")
        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(self.nested_file_path))
    
    def test_append_to_file(self):
        # Test appending to an existing file
        append_content = "Appended line 1\nAppended line 2\n"
        original_content = ""
        with open(self.small_file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        result = append_to_file(self.small_file_path, append_content)
        self.assertTrue(result["success"])
        
        # Verify content was appended
        with open(self.small_file_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
        self.assertEqual(new_content, original_content + append_content)
        
        # Test appending to a non-existent file
        result = append_to_file(self.nonexistent_file_path, "This file should be created.")
        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(self.nonexistent_file_path))
    
    def test_insert_at_line(self):
        # Test inserting at the beginning
        result = insert_at_line(self.small_file_path, 1, "Inserted at beginning\n")
        self.assertTrue(result["success"])
        
        # Verify insertion
        with open(self.small_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        self.assertEqual(lines[0], "Inserted at beginning\n")
        self.assertEqual(len(lines), 4)  # Original 3 lines + 1 inserted
        
        # Test inserting in the middle
        result = insert_at_line(self.small_file_path, 3, "Inserted in middle\n")
        self.assertTrue(result["success"])
        
        # Verify insertion
        with open(self.small_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        self.assertEqual(lines[2], "Inserted in middle\n")
        self.assertEqual(len(lines), 5)  # Now 5 lines
        
        # Test inserting at the end
        result = insert_at_line(self.small_file_path, 6, "Inserted at end\n")
        self.assertTrue(result["success"])
        
        # Verify insertion
        with open(self.small_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        self.assertEqual(lines[5], "Inserted at end\n")
        self.assertEqual(len(lines), 6)
        
        # Test inserting at invalid line number
        result = insert_at_line(self.small_file_path, 0, "Should fail")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid line number")
        
        # Test inserting in non-existent file
        result = insert_at_line(self.nonexistent_file_path, 1, "Creating new file")
        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(self.nonexistent_file_path))
    
    def test_delete_line(self):
        # First, create a test file with known content
        test_file_path = os.path.join(self.test_dir, "delete_test.txt")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
            
        # Test deleting a line in the middle
        result = delete_line(test_file_path, 3)
        self.assertTrue(result["success"])
        
        # Verify line was deleted
        with open(test_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0], "Line 1\n")
        self.assertEqual(lines[1], "Line 2\n")
        self.assertEqual(lines[2], "Line 4\n")  # Line 3 is gone
        
        # Test deleting the first line
        result = delete_line(test_file_path, 1)
        self.assertTrue(result["success"])
        
        # Verify line was deleted
        with open(test_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "Line 2\n")
        
        # Test invalid line number
        result = delete_line(test_file_path, 10)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid line number")
        
        # Test invalid negative line number
        result = delete_line(test_file_path, -1)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid line number")
        
        # Test non-existent file
        result = delete_line(self.nonexistent_file_path, 1)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "File not found")


if __name__ == "__main__":
    unittest.main() 