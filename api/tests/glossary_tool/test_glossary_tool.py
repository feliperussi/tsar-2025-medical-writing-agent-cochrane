import pytest
import pytest_asyncio
from api.tools.glossary_tool import GlossaryTool
from api.schemas.base import ToolInfo, ToolResponse


@pytest.fixture
def glossary_tool():
    """Create a glossary tool instance"""
    return GlossaryTool()


class TestGlossaryTool:
    """Test the GlossaryTool class"""
    
    def test_tool_info(self, glossary_tool):
        """Test that tool info is correctly defined"""
        info = glossary_tool.info
        
        assert isinstance(info, ToolInfo)
        assert info.name == "glossary"
        assert info.description == "Find and define complex medical phrases within a body of text with location information"
        assert info.version == "2.0.0"
        
        # Check parameters
        assert "properties" in info.parameters
        assert "text" in info.parameters["properties"]
        assert info.parameters["required"] == ["text"]
    
    @pytest.mark.asyncio
    async def test_execute_success(self, glossary_tool):
        """Test successful execution with medical text"""
        parameters = {
            "text": "The patient has diabetes and hypertension."
        }
        
        response = await glossary_tool.execute(parameters)
        
        assert isinstance(response, ToolResponse)
        assert response.tool_name == "glossary"
        assert response.status == "success"
        assert response.error is None
        assert response.result is not None
        
        # Check result structure
        assert "analysis_summary" in response.result
        assert "found_terms" in response.result
        assert response.result["analysis_summary"]["total_unique_phrases_found"] > 0
    
    @pytest.mark.asyncio
    async def test_execute_empty_text(self, glossary_tool):
        """Test execution with empty text"""
        parameters = {"text": ""}
        
        response = await glossary_tool.execute(parameters)
        
        assert response.status == "success"
        assert response.result["analysis_summary"]["total_unique_phrases_found"] == 0
        assert len(response.result["found_terms"]) == 0
    
    @pytest.mark.asyncio
    async def test_execute_missing_parameter(self, glossary_tool):
        """Test execution with missing required parameter"""
        parameters = {}
        
        response = await glossary_tool.execute(parameters)
        
        assert response.status == "error"
        assert response.error == "Missing required parameter: text"
        assert response.result is None
    
    @pytest.mark.asyncio
    async def test_execute_with_multiple_phrases(self, glossary_tool):
        """Test execution with text containing multiple medical phrases"""
        parameters = {
            "text": "During the clinical trial, patients with chronic disease experienced adverse effects from the new medication."
        }
        
        response = await glossary_tool.execute(parameters)
        
        assert response.status == "success"
        found_terms = response.result["found_terms"]
        
        # Check that expected phrases were found
        expected_phrases = ["clinical trial", "adverse effects", "medication"]
        found_main_terms = [term["main_term"].lower() for term in found_terms]
        
        for phrase in expected_phrases:
            assert any(phrase in term for term in found_main_terms)
        
        # Check term structure
        for term in found_terms:
            assert "main_term" in term
            assert "definitions" in term
            assert "matches_in_text" in term
            
            # Check definition structure
            for definition in term["definitions"]:
                assert "plain_alternative" in definition
                assert "source" in definition
    
    @pytest.mark.asyncio
    async def test_execute_case_insensitive(self, glossary_tool):
        """Test that phrase matching is case insensitive"""
        parameters = {
            "text": "The patient has DIABETES and Hypertension."
        }
        
        response = await glossary_tool.execute(parameters)
        
        assert response.status == "success"
        found_terms = response.result["found_terms"]
        
        # Both should be found despite different cases
        found_main_terms = [term["main_term"].lower() for term in found_terms]
        assert any("diabetes" in term for term in found_main_terms)
        assert any("hypertension" in term for term in found_main_terms)
    
    def test_validate_parameters(self, glossary_tool):
        """Test parameter validation"""
        # Valid parameters
        assert glossary_tool.validate_parameters({"text": "test"}) is True
        
        # Missing required parameter
        assert glossary_tool.validate_parameters({}) is False
        assert glossary_tool.validate_parameters({"wrong_param": "test"}) is False