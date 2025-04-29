# Web Search and Save Integration Tests

This directory contains integration tests for the web search and file saving functionality.

## Prerequisites

- Python 3.7+
- pytest
- All requirements for the main application installed

## Running the Tests

To run all tests:

```bash
pytest -v tests/test_web_search_save.py
```

To run a specific test:

```bash
pytest -v tests/test_web_search_save.py::test_basic_web_search_and_save
```

To run tests in offline mode (skipping tests that require internet):

```bash
pytest -v tests/test_web_search_save.py --offline
```

## Test Cases

The integration tests cover the following scenarios:

1. **Basic Web Search and Save**: Tests basic search functionality and saving results to a file
2. **Multiple Queries**: Tests searching for multiple topics and saving to different files
3. **Specific Information Extraction**: Tests extracting specific information from search results
4. **Search with Date Filtering**: Tests searching for recent information with date filtering
5. **Error Handling**: Tests how the script handles invalid queries or paths
6. **Structured Data Extraction**: Tests searching for information and saving as structured JSON data

## Output Files

By default, test output files are saved to the `output/tests` directory. 
If you want to inspect the search results after running the tests, comment out the cleanup code in the `output_dir` fixture.

## Test Configuration

- All tests that require network access are marked with the `@pytest.mark.network` decorator
- You can skip tests requiring internet by using the `--offline` flag
- The `conftest.py` file contains common pytest configurations and fixtures

## Notes

- These tests require an internet connection to perform the web searches
- The tests may occasionally fail if search results change or if there are network issues
- Some tests may take longer to complete as they involve real web searches 