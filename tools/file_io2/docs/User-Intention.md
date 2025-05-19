# File I/O MCP Tool Requirements

## Overview
This MCP tool provides text file I/O operations, specifically designed for large language models with context window limitations. It enables reading and writing operations for text files, with features to handle files of various sizes.

## Location
- MCP tool location: `tools/file_io2`

## Functionality Requirements

### Reading Operations
1. Get total line count of a file
2. Read content from a specified line range
3. Read file in chunks (to allow LLM to process large files)
4. Read file with line numbers (starting from 1)

### Writing Operations
1. Append content to the end of a file
2. Insert content at a specified line while preserving other content
3. Create a new file and write content when file doesn't exist
4. Check if a file exists
5. Delete specified lines

### Additional Requirements

#### Error Handling and Guidance
- Clear error messages for common issues (file not found, permission denied)
- Guidance for LLM on how to correct requests when errors occur

#### Parameter Validation and Edge Cases
- Validation for line number ranges (negative numbers, out of range)
- Handling of empty files

#### Path Safety
- Prevention of path traversal attacks
- Support for both relative and absolute paths
- Automatic creation of parent directories when needed

## Tool Function Breakdown

1. **File Information Functions**
   - `check_file_exists`: Check if a file exists
   - `get_file_line_count`: Get the total number of lines in a file

2. **File Reading Functions**
   - `read_file_range`: Read content from a specified line range
   - `read_file_chunks`: Read file in chunks with metadata
   - `read_file_with_line_numbers`: Read file with line numbers

3. **File Writing Functions**
   - `create_or_write_file`: Create or overwrite a file with content
   - `append_to_file`: Append content to the end of a file
   - `insert_at_line`: Insert content at a specified line
   - `delete_line`: Delete specified line(s)

## Specific Implementation Details

### `read_file_chunks` Implementation
- **Parameters**:
  - `file_path`: Path to the file
  - `chunk_size`: Number of lines per chunk
  - `overlap`: Optional, number of overlapping lines between chunks (default: 0)
  - `chunk_index`: Optional, specific chunk to retrieve

- **Logic**:
  - Get total line count
  - Calculate total number of chunks
  - Return specific chunk content if chunk_index is provided
  - Otherwise return metadata about all chunks

- **Return Format**:
  - Single chunk mode: Content of the specified chunk with metadata
  - Summary mode: Information about all chunks including line ranges 