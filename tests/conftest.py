"""
Shared pytest fixtures and configuration
"""
import pytest
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def setup_logging():
    """Setup logging for all tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("pytest")

@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture(scope="session")
def app_data_dir(project_root):
    """Get the app_data directory path"""
    return os.path.join(project_root, "app_data") 