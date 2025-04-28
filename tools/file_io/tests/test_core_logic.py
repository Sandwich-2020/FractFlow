"""
Core Logic Unit Tests

This module contains unit tests for the core_logic.py module, testing all file I/O
operations like reading, writing, copying, moving, and deleting files and directories.

The tests use pytest and the pytest-asyncio plugin to test asynchronous functions.
Each test is isolated using temporary directories to avoid affecting the actual file system.

Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-27
License: MIT License
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the Python path so we can import modules from there
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core_logic import (
    read_file,
    write_file,
    list_directory,
    delete_file,
    move_file,
    copy_file,
    file_exists,
    get_file_info,
    insert_file
)

# ===== PYTEST EXPLANATIONS =====
# 
# pytest is a testing framework for Python that makes it easy to write simple
# and scalable test cases. Here's how it works in this file:
#
# 1. FIXTURES (@pytest.fixture):
#    - Fixtures are functions that provide a fixed baseline for tests
#    - They set up any required resources before tests and clean up after tests
#    - They're defined using the @pytest.fixture decorator
#    - Fixtures can be requested by test functions by adding their names as parameters
#
# 2. ASYNCIO TESTING (@pytest.mark.asyncio):
#    - This marker tells pytest that the test function is an async function
#    - It enables proper async/await execution and handling in the test
#    - Requires the pytest-asyncio plugin to be installed
#    - Allows testing of async functions using the "await" keyword
#
# 3. TEST DISCOVERY:
#    - pytest automatically discovers tests in files named "test_*.py" or "*_test.py"
#    - Functions prefixed with "test_" are identified as test cases
#
# 4. ASSERTIONS:
#    - pytest uses Python's standard "assert" statement for verification
#    - It provides rich comparison details when assertions fail
#

@pytest.fixture
def temp_dir():
    """
    A pytest fixture that creates a temporary directory for testing.
    
    This fixture:
    1. Creates a new temporary directory before each test that uses it
    2. Yields the directory path to the test function
    3. Cleans up by removing the directory after the test completes
    
    The 'yield' statement is key - everything before it runs before the test,
    everything after it runs after the test (cleanup phase)
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir  # This provides the fixture value to the test function
    
    # Cleanup after the test is done (even if it fails)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_read_write_file(temp_dir):
    """
    Test reading and writing a file.
    
    This test:
    1. Requests the temp_dir fixture to get a safe directory for testing
    2. Uses @pytest.mark.asyncio to enable testing of async functions
    3. Tests both write_file and read_file functionality together
    4. Uses assertions to verify the expected behavior
    """
    file_path = os.path.join(temp_dir, "test.txt")
    content = "Hello, world!"
    
    # Test write
    result = await write_file(file_path, content)
    assert result is True  # Check the function returned True
    assert os.path.exists(file_path)  # Verify the file was actually created
    
    # Test read
    read_content = await read_file(file_path)
    assert read_content == content  # Verify the content matches what we wrote

@pytest.mark.asyncio
async def test_binary_read_write(temp_dir):
    """
    Test reading and writing binary data.
    
    This demonstrates:
    1. Testing the binary mode options of read_file and write_file
    2. Using binary data (bytes objects) instead of strings
    3. Verifying binary content is preserved exactly
    """
    file_path = os.path.join(temp_dir, "test.bin")
    content = b'\x00\x01\x02\x03'  # Binary data
    
    # Test write in binary mode
    result = await write_file(file_path, content, binary=True)
    assert result is True
    
    # Test read in binary mode
    read_content = await read_file(file_path, binary=True)
    assert read_content == content  # Binary content should match exactly

@pytest.mark.asyncio
async def test_list_directory(temp_dir):
    """
    Test listing directory contents.
    
    This test:
    1. Sets up a test directory with files and subdirectories
    2. Calls list_directory to get the contents
    3. Verifies the returned data contains the expected items
    4. Checks that the metadata (like is_dir flag) is correct
    """
    # Create some files
    file1 = os.path.join(temp_dir, "file1.txt")
    file2 = os.path.join(temp_dir, "file2.txt")
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir)
    
    with open(file1, "w") as f:
        f.write("file1")
    with open(file2, "w") as f:
        f.write("file2")
    
    # Test list_directory
    items = await list_directory(temp_dir)
    assert len(items) == 3  # Should find 3 items (2 files, 1 directory)
    
    # Extract just the names for easier checking
    names = [item["name"] for item in items]
    assert "file1.txt" in names
    assert "file2.txt" in names
    assert "subdir" in names
    
    # Check that types are correctly identified
    for item in items:
        if item["name"] == "subdir":
            assert item["is_dir"] is True  # Should be identified as a directory
        else:
            assert item["is_dir"] is False  # Should be identified as files

@pytest.mark.asyncio
async def test_delete_file(temp_dir):
    """
    Test deleting a file.
    
    This test:
    1. Creates a test file
    2. Calls delete_file to remove it
    3. Verifies the file no longer exists
    """
    file_path = os.path.join(temp_dir, "to_delete.txt")
    with open(file_path, "w") as f:
        f.write("delete me")
    
    # Verify the file exists before deletion
    assert os.path.exists(file_path)
    
    # Test delete
    result = await delete_file(file_path)
    assert result is True  # Function should report success
    assert not os.path.exists(file_path)  # File should be gone

@pytest.mark.asyncio
async def test_delete_directory(temp_dir):
    """
    Test deleting a directory with contents.
    
    This test:
    1. Creates a directory with a file inside
    2. Calls delete_file on the directory
    3. Verifies the directory and its contents are removed
    """
    subdir = os.path.join(temp_dir, "to_delete_dir")
    os.makedirs(subdir)
    file_in_dir = os.path.join(subdir, "file.txt")
    with open(file_in_dir, "w") as f:
        f.write("delete me")
    
    # Verify the directory exists before deletion
    assert os.path.exists(subdir)
    
    # Test delete
    result = await delete_file(subdir)
    assert result is True  # Function should report success
    assert not os.path.exists(subdir)  # Directory should be gone

@pytest.mark.asyncio
async def test_move_file(temp_dir):
    """
    Test moving a file from one location to another.
    
    This test:
    1. Creates a source file with content
    2. Calls move_file to relocate it
    3. Verifies the file is gone from the source
    4. Verifies the file exists at the destination
    5. Checks the content is preserved
    """
    source = os.path.join(temp_dir, "source.txt")
    dest = os.path.join(temp_dir, "dest.txt")
    
    with open(source, "w") as f:
        f.write("move me")
    
    # Test move
    result = await move_file(source, dest)
    assert result is True  # Function should report success
    assert not os.path.exists(source)  # Source file should be gone
    assert os.path.exists(dest)  # Destination file should exist
    
    # Check content was preserved
    with open(dest, "r") as f:
        content = f.read()
    assert content == "move me"

@pytest.mark.asyncio
async def test_copy_file(temp_dir):
    """
    Test copying a file from one location to another.
    
    This test:
    1. Creates a source file with content
    2. Calls copy_file to duplicate it
    3. Verifies the source still exists (unlike move)
    4. Verifies the destination also exists
    5. Checks the content is preserved
    """
    source = os.path.join(temp_dir, "source.txt")
    dest = os.path.join(temp_dir, "dest.txt")
    
    with open(source, "w") as f:
        f.write("copy me")
    
    # Test copy
    result = await copy_file(source, dest)
    assert result is True  # Function should report success
    assert os.path.exists(source)  # Source should still exist
    assert os.path.exists(dest)  # Destination should also exist
    
    # Check content was preserved
    with open(dest, "r") as f:
        content = f.read()
    assert content == "copy me"

@pytest.mark.asyncio
async def test_file_exists(temp_dir):
    """
    Test checking if a file exists.
    
    This test:
    1. Creates a test file
    2. Calls file_exists on that path and a non-existent path
    3. Verifies the function correctly identifies both cases
    """
    file_path = os.path.join(temp_dir, "exists.txt")
    with open(file_path, "w") as f:
        f.write("I exist")
    
    # Test exists on existing file
    result = await file_exists(file_path)
    assert result is True  # Should return True for existing file
    
    # Test non-existent file
    result = await file_exists(os.path.join(temp_dir, "nonexistent.txt"))
    assert result is False  # Should return False for non-existent file

@pytest.mark.asyncio
async def test_get_file_info(temp_dir):
    """
    Test getting file metadata information.
    
    This test:
    1. Creates a test file
    2. Calls get_file_info to retrieve its metadata
    3. Verifies all the expected fields are present and correct
    4. Also tests with a directory to ensure it's handled differently
    """
    file_path = os.path.join(temp_dir, "info.txt")
    with open(file_path, "w") as f:
        f.write("Get my info")
    
    # Test info on a file
    info = await get_file_info(file_path)
    assert info["name"] == "info.txt"  # Filename should match
    assert info["path"] == file_path  # Path should match
    assert info["is_dir"] is False  # Should be identified as a file
    assert info["size"] == 11  # Length of "Get my info"
    assert info["extension"] == ".txt"  # Extension should be extracted
    
    # Test info on a directory
    dir_info = await get_file_info(temp_dir)
    assert dir_info["is_dir"] is True  # Should be identified as a directory
    assert dir_info["extension"] is None  # Directories have no extensions 

# Import the insert_file function
from src.core_logic import insert_file

@pytest.mark.asyncio
async def test_insert_file_by_line(temp_dir):
    """
    Test inserting content into a file by line number.
    
    This test:
    1. Creates a test file with multiple lines
    2. Inserts new content at a specific line
    3. Verifies the content was inserted correctly
    4. Tests different line positions (beginning, middle, end)
    """
    file_path = os.path.join(temp_dir, "insert_test.txt")
    
    # Create a test file with multiple lines
    original_content = "Line 1\nLine 2\nLine 4"
    with open(file_path, "w") as f:
        f.write(original_content)
    
    # Insert at line 3 (between Line 2 and Line 4)
    new_line = "Line 3"
    result = await insert_file(file_path, new_line, 3, by_line=True)
    assert result is True
    
    # Read the file and verify content
    with open(file_path, "r") as f:
        content = f.read()
    
    expected = "Line 1\nLine 2\nLine 3\nLine 4"
    assert content == expected
    
    # Test inserting at the beginning (line 1)
    result = await insert_file(file_path, "First Line", 1, by_line=True)
    with open(file_path, "r") as f:
        content = f.read()
    
    assert content.startswith("First Line\nLine 1")
    
    # Test inserting at the end (beyond last line)
    result = await insert_file(file_path, "Last Line", 10, by_line=True)
    with open(file_path, "r") as f:
        content = f.read()
    
    assert content.endswith("Line 4\nLast Line")

@pytest.mark.asyncio
async def test_insert_file_by_offset(temp_dir):
    """
    Test inserting content into a file by byte offset.
    
    This test:
    1. Creates a test file with content
    2. Inserts new content at a specific byte offset
    3. Verifies the content was inserted correctly
    """
    file_path = os.path.join(temp_dir, "insert_offset.txt")
    
    # Create a test file
    original_content = "Hello, world!"
    with open(file_path, "w") as f:
        f.write(original_content)
    
    # Insert at offset 7 (after "Hello, ")
    result = await insert_file(file_path, "beautiful ", 7)
    assert result is True
    
    # Read the file and verify content
    with open(file_path, "r") as f:
        content = f.read()
    
    expected = "Hello, beautiful world!"
    assert content == expected
    
    # Test inserting at the beginning (offset 0)
    result = await insert_file(file_path, "Oh, ", 0)
    with open(file_path, "r") as f:
        content = f.read()
    
    assert content == "Oh, Hello, beautiful world!"

@pytest.mark.asyncio
async def test_insert_file_by_pattern(temp_dir):
    """
    Test inserting content into a file after a pattern.
    
    This test:
    1. Creates a test file with content
    2. Inserts new content after a specific pattern
    3. Verifies the content was inserted correctly
    4. Tests error handling for non-existent patterns
    """
    file_path = os.path.join(temp_dir, "insert_pattern.txt")
    
    # Create a test file
    original_content = "This is a test for pattern insertion."
    with open(file_path, "w") as f:
        f.write(original_content)
    
    # Insert after pattern "a test"
    result = await insert_file(file_path, " case", "a test")
    assert result is True
    
    # Read the file and verify content
    with open(file_path, "r") as f:
        content = f.read()
    
    expected = "This is a test case for pattern insertion."
    assert content == expected
    
    # Test non-existent pattern
    with pytest.raises(ValueError) as excinfo:
        await insert_file(file_path, "content", "nonexistent pattern")
    
    assert "not found" in str(excinfo.value)

@pytest.mark.asyncio
async def test_insert_file_binary(temp_dir):
    """
    Test inserting binary content into a file.
    
    This test:
    1. Creates a test binary file
    2. Inserts binary content at a specific position
    3. Verifies the content was inserted correctly
    """
    file_path = os.path.join(temp_dir, "binary.bin")
    
    # Create a binary file
    binary_content = b'\x01\x02\x03\x05'
    with open(file_path, "wb") as f:
        f.write(binary_content)
    
    # Insert binary content after byte 3
    insert_content = b'\x04'
    result = await insert_file(file_path, insert_content, 3, binary=True)
    assert result is True
    
    # Read the file and verify content
    with open(file_path, "rb") as f:
        content = f.read()
    
    expected = b'\x01\x02\x03\x04\x05'
    assert content == expected 