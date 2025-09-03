import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.core.tool_registry import tool_registry
from api.tools.glossary_tool import GlossaryTool
from api.core.glossary_singleton import glossary_singleton


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_tools():
    """Ensure tools are registered before tests"""
    # Clear existing tools
    tool_registry._tools.clear()
    
    # Register tools
    glossary_tool = GlossaryTool()
    tool_registry.register(glossary_tool)
    
    yield
    
    # Clean up after tests
    tool_registry._tools.clear()


@pytest.fixture(scope="session", autouse=True)
def teardown_singleton():
    """Reset singleton at the end of test session"""
    yield
    # Reset singleton after all tests
    glossary_singleton.reset()


@pytest.fixture
def sample_medical_text():
    """Sample medical text for testing"""
    return "The patient experienced adverse effects during the clinical trial and was diagnosed with diabetes."


@pytest.fixture
def sample_medical_text_with_hypertension():
    """Another sample medical text"""
    return "The patient has hypertension and was prescribed medication for treatment."