import pytest
import os
import sys
from pathlib import Path

# Add project root to path for imports
@pytest.fixture(scope="session", autouse=True)
def setup_path():
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Ensure test directory exists
    test_output = project_root / "output" / "tests"
    test_output.mkdir(exist_ok=True, parents=True)
    
    yield
    
    # Cleanup is handled in individual test fixtures

# Skip tests that require network if offline mode is enabled
def pytest_addoption(parser):
    parser.addoption(
        "--offline", action="store_true", default=False, 
        help="Run tests in offline mode (skip tests requiring internet)"
    )

def pytest_collection_modifyitems(config, items):
    if config.getoption("--offline"):
        skip_network = pytest.mark.skip(reason="Test requires internet connection")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(skip_network)

# Mark tests that require network
def pytest_configure(config):
    config.addinivalue_line("markers", "network: mark test as requiring internet connection") 