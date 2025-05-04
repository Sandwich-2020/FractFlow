import os
import subprocess
import time
import json
import pytest
from pathlib import Path

# Define the path to the script
SCRIPT_PATH = "scripts/run_save_web_search_to_file.py"

@pytest.fixture
def output_dir():
    """Fixture to create and clean up a temporary output directory"""
    test_output_dir = Path("output/tests")
    test_output_dir.mkdir(exist_ok=True, parents=True)
    yield test_output_dir
    # Comment out the following line if you want to keep the test outputs for inspection
    # for file in test_output_dir.glob("*"):
    #     file.unlink()
    # test_output_dir.rmdir()

@pytest.mark.network
def test_basic_web_search_and_save(output_dir):
    """Test basic web search and save functionality"""
    output_file = output_dir / "basic_search_result.txt"
    
    # Run the script with a basic query
    query = "What is Python programming language?"
    cmd = [
        "python", SCRIPT_PATH, 
        "--user_query", f"Search for '{query}' and save the results to {output_file}"
    ]
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    
    # Check if the process executed successfully
    assert process.returncode == 0
    
    # Check if the output file was created
    assert output_file.exists()
    
    # Check if the output file contains relevant content
    content = output_file.read_text()
    assert "Python" in content
    assert len(content) > 100  # Ensure we have a substantial response

@pytest.mark.network
def test_multiple_queries(output_dir):
    """Test searching for multiple topics and saving to different files"""
    topics = ["Artificial Intelligence", "Machine Learning", "Deep Learning"]
    output_files = [output_dir / f"{topic.lower().replace(' ', '_')}_results.txt" for topic in topics]
    
    for topic, output_file in zip(topics, output_files):
        cmd = [
            "python", SCRIPT_PATH, 
            "--user_query", f"Search about {topic} and save the detailed information to {output_file}"
        ]
        
        process = subprocess.run(cmd, capture_output=True, text=True)
        assert process.returncode == 0
        assert output_file.exists()
        
        # Check content relevance
        content = output_file.read_text()
        assert any(keyword in content for keyword in topic.split())
        assert len(content) > 100

@pytest.mark.network
def test_specific_information_extraction(output_dir):
    """Test extracting specific information from search results"""
    output_file = output_dir / "python_versions.txt"
    
    query = "What are the main differences between Python 2 and Python 3?"
    cmd = [
        "python", SCRIPT_PATH, 
        "--user_query", f"Research '{query}' and save a summary of key differences to {output_file}"
    ]
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert process.returncode == 0
    assert output_file.exists()
    
    # Check content for relevance
    content = output_file.read_text()
    assert "Python 2" in content and "Python 3" in content
    assert "differences" in content.lower() or "changes" in content.lower()

@pytest.mark.network
def test_search_with_date_filtering(output_dir):
    """Test searching for recent information with date filtering"""
    output_file = output_dir / "recent_ai_developments.txt"
    
    # Get current year
    current_year = time.strftime("%Y")
    
    query = f"Recent developments in AI in {current_year}"
    cmd = [
        "python", SCRIPT_PATH, 
        "--user_query", f"Search for '{query}' and save only information from {current_year} to {output_file}"
    ]
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert process.returncode == 0
    assert output_file.exists()
    
    # Check for current year references
    content = output_file.read_text()
    assert current_year in content
    assert "AI" in content or "Artificial Intelligence" in content

@pytest.mark.network
def test_error_handling(output_dir):
    """Test how the script handles invalid queries or paths"""
    # Invalid output directory
    invalid_output = "/nonexistent/directory/output.txt"
    cmd = [
        "python", SCRIPT_PATH, 
        "--user_query", f"Search for 'Python' and save results to {invalid_output}"
    ]
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    # The process should still complete, but there might be error messages
    assert "error" in process.stderr.lower() or "failed" in process.stderr.lower()
    
    # Check that the agent appropriately handles the error in its response
    assert "cannot" in process.stdout.lower() or "unable" in process.stdout.lower() or "error" in process.stdout.lower()

@pytest.mark.network
def test_structured_data_extraction_to_json(output_dir):
    """Test searching for information and saving as structured JSON"""
    output_file = output_dir / "top_programming_languages.json"
    
    cmd = [
        "python", SCRIPT_PATH, 
        "--user_query", f"Search for the top 5 programming languages in 2023 by popularity. Find their creator, year created, and main use cases. Save this as a structured JSON array to {output_file}"
    ]
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert process.returncode == 0
    assert output_file.exists()
    
    # Validate the JSON structure
    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
            
        # Check if it's an array with at least some entries
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check if each entry has the expected fields
        for language in data:
            assert "name" in language
            # Some fields might be missing due to search results, so we're lenient
            assert any(key in language for key in ["creator", "year", "use_cases"])
            
    except json.JSONDecodeError:
        # If not valid JSON, the test fails but with a more informative message
        content = output_file.read_text()
        pytest.fail(f"Output file is not valid JSON. Content: {content[:100]}...") 