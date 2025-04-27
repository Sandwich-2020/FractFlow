"""
Run Server Integration Tests

This module contains integration tests for the file_io tool server.
Tests interact with the server through the command-line interface, 
sending queries and verifying that the operations are properly executed on the file system.

These tests use temporary directories to ensure they don't affect the actual file system and
clean up after themselves.

Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-27
License: MIT License
"""

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

# Add project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)


@pytest.fixture
def temp_test_dir():
    """Create temporary test directory and clean up after the test"""
    temp_dir = tempfile.mkdtemp()
    
    # Create some test files
    test_file = os.path.join(temp_dir, "test_file.txt")
    with open(test_file, "w") as f:
        f.write("This is test content for integration tests")
    
    # Create a subdirectory
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir)
    with open(os.path.join(subdir, "subfile.txt"), "w") as f:
        f.write("This is a file in a subdirectory")
    
    yield temp_dir
    
    # Clean up
    shutil.rmtree(temp_dir)


def run_query(query):
    """
    Run a single query and return the result
    
    Args:
        query: Query string to send to run_server.py
        
    Returns:
        str: Command output
    """
    # Determine the path to run_server.py
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run_server.py")
    
    # Use subprocess to execute the command
    process = subprocess.Popen(
        [sys.executable, script_path, "--user_query", query],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        universal_newlines=True
    )
    
    # Capture output
    stdout, stderr = process.communicate(timeout=60)
    
    # Check for errors
    if process.returncode != 0:
        print(f"Error executing command: {stderr}")
    
    # Extract the result (remove thinking and other non-result output)
    result_match = re.search(r"Result:\s+(.*?)(?:\n\nAgent session ended\.)?$", stdout, re.DOTALL)
    if result_match:
        return result_match.group(1).strip()
    
    return stdout


def test_read_file_query(temp_test_dir):
    """Test query for reading a file"""
    test_file = os.path.join(temp_test_dir, "test_file.txt")
    
    # Run the query
    query = f"Read the file {test_file} and tell me its content"
    result = run_query(query)
    
    # Verify that the result contains the file content
    assert "test content for integration tests" in result


def test_write_file_query(temp_test_dir):
    """Test query for writing to a file"""
    new_file = os.path.join(temp_test_dir, "new_file.txt")
    content = "This is new content created during integration testing"
    
    # Run the query
    query = f"Create a new file at {new_file} with this content: '{content}'"
    result = run_query(query)
    
    # Verify the file was created
    assert os.path.exists(new_file)
    
    # Verify the content is correct
    with open(new_file, "r") as f:
        file_content = f.read()
    assert content in file_content


def test_list_directory_query(temp_test_dir):
    """Test query for listing directory contents"""
    # Run the query
    query = f"List all files and directories in {temp_test_dir}"
    result = run_query(query)
    
    # Verify the result includes known files
    assert "test_file.txt" in result
    assert "subdir" in result


def test_file_info_query(temp_test_dir):
    """Test query for getting file information"""
    test_file = os.path.join(temp_test_dir, "test_file.txt")
    
    # Run the query - only request specific fields
    query = f"Get information about {test_file}, only return the name, size and extension"
    result = run_query(query)
    
    # Verify the result contains the requested information
    assert "test_file.txt" in result
    assert "size" in result.lower()
    assert ".txt" in result.lower()


def test_copy_file_query(temp_test_dir):
    """Test query for copying a file"""
    source_file = os.path.join(temp_test_dir, "test_file.txt")
    dest_file = os.path.join(temp_test_dir, "copied_file.txt")
    
    # Run the query
    query = f"Copy the file from {source_file} to {dest_file}"
    result = run_query(query)
    
    # Verify the file was copied
    assert os.path.exists(dest_file)
    
    # Verify the content matches
    with open(source_file, "r") as src, open(dest_file, "r") as dst:
        assert src.read() == dst.read()


def test_move_file_query(temp_test_dir):
    """Test query for moving a file"""
    # First create a file to move
    source_file = os.path.join(temp_test_dir, "to_move.txt")
    with open(source_file, "w") as f:
        f.write("This file will be moved")
    
    dest_file = os.path.join(temp_test_dir, "moved_file.txt")
    
    # Run the query
    query = f"Move the file {source_file} to {dest_file}"
    result = run_query(query)
    
    # Verify the file was moved
    assert not os.path.exists(source_file)
    assert os.path.exists(dest_file)


def test_delete_file_query(temp_test_dir):
    """Test query for deleting a file"""
    # Create a file to delete
    file_to_delete = os.path.join(temp_test_dir, "to_delete.txt")
    with open(file_to_delete, "w") as f:
        f.write("This file will be deleted")
    
    # Verify the file exists
    assert os.path.exists(file_to_delete)
    
    # Run the query
    query = f"Delete the file at {file_to_delete}"
    result = run_query(query)
    
    # Verify the file was deleted
    assert not os.path.exists(file_to_delete)


def test_exists_query(temp_test_dir):
    """Test query for checking if a file exists"""
    existing_file = os.path.join(temp_test_dir, "test_file.txt")
    nonexistent_file = os.path.join(temp_test_dir, "does_not_exist.txt")
    
    # Run the query - existing file
    query = f"Check if the file {existing_file} exists"
    result = run_query(query)
    
    # Verify the result indicates the file exists
    assert "exists" in result.lower() or "true" in result.lower()
    
    # Run the query - non-existent file
    query = f"Check if the file {nonexistent_file} exists"
    result = run_query(query)
    
    # Verify the result indicates the file does not exist
    assert "not" in result.lower() or "false" in result.lower()


def test_complex_query(temp_test_dir):
    """Test complex multi-step query"""
    # Create a subdirectory for moving files
    new_dir = os.path.join(temp_test_dir, "new_directory")
    source_file = os.path.join(temp_test_dir, "test_file.txt")
    dest_file = os.path.join(new_dir, "moved_test_file.txt")
    
    # Run the query - create directory
    query1 = f"Create a directory at {new_dir}"
    run_query(query1)
    
    # Verify the directory was created
    assert os.path.exists(new_dir)
    assert os.path.isdir(new_dir)
    
    # Run the query - move file to new directory
    query2 = f"Move the file {source_file} to {dest_file}"
    run_query(query2)
    
    # Verify the file was moved
    assert not os.path.exists(source_file)
    assert os.path.exists(dest_file)
    
    # Run the query - list new directory contents
    query3 = f"List all files in {new_dir}"
    result = run_query(query3)
    
    # Verify the result shows the moved file
    assert "moved_test_file.txt" in result


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 