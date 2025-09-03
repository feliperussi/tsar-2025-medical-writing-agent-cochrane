"""
Unit tests for the linguistic analysis tool (not API endpoints)
"""

import pytest
from api.tools.linguistic_analysis_tool import LinguisticAnalysisTool


class TestLinguisticAnalysisToolUnit:
    """Unit tests for the linguistic analysis tool itself"""
    
    @pytest.fixture
    def tool(self):
        """Create a tool instance for testing"""
        return LinguisticAnalysisTool()
    
    def test_tool_info(self, tool):
        """Test that tool info is properly configured"""
        info = tool.info
        
        assert info.name == "linguistic_analysis"
        assert "linguistic analysis" in info.description.lower()
        assert "properties" in info.parameters
        assert info.version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_single_text_analysis(self, tool):
        """Test single text analysis"""
        parameters = {
            "text": "The patient was treated by the doctor.",
            "include_tokens": False
        }
        
        response = await tool.execute(parameters)
        
        assert response.tool_name == "linguistic_analysis"
        assert response.status == "success"
        assert response.error is None
        assert response.result is not None
        
        # Check result structure
        result = response.result
        assert "words" in result
        assert "sentences" in result
        assert result["sentences"] == 1
        assert result["passive_voice"] >= 1  # "was treated"
    
    @pytest.mark.asyncio
    async def test_detailed_analysis(self, tool):
        """Test analysis with detailed tokens"""
        parameters = {
            "text": "The patient was treated by the doctor.",
            "include_tokens": True
        }
        
        response = await tool.execute(parameters)
        
        assert response.status == "success"
        result = response.result
        
        # Check that detailed tokens are included
        assert "detailed_tokens" in result
        detailed_tokens = result["detailed_tokens"]
        
        assert "passive_voice_tokens" in detailed_tokens
        assert "noun_tokens" in detailed_tokens
        assert len(detailed_tokens["passive_voice_tokens"]) >= 1
    
    @pytest.mark.asyncio
    async def test_multiple_texts_analysis(self, tool):
        """Test multiple texts analysis"""
        parameters = {
            "texts": [
                "Simple sentence.",
                "The complex medical intervention was successfully implemented."
            ],
            "text_ids": ["simple", "complex"],
            "include_tokens": False
        }
        
        response = await tool.execute(parameters)
        
        assert response.status == "success"
        result = response.result
        
        assert "analyses" in result
        assert "summary" in result
        
        analyses = result["analyses"]
        assert len(analyses) == 2
        assert analyses[0]["text_id"] == "simple"
        assert analyses[1]["text_id"] == "complex"
    
    @pytest.mark.asyncio
    async def test_empty_text_error(self, tool):
        """Test error handling for missing text"""
        parameters = {}
        
        response = await tool.execute(parameters)
        
        assert response.status == "error"
        assert "required" in response.error.lower()
    
    @pytest.mark.asyncio
    async def test_invalid_texts_type(self, tool):
        """Test error handling for invalid texts type"""
        parameters = {
            "texts": "not a list"
        }
        
        response = await tool.execute(parameters)
        
        assert response.status == "error"
        assert "array" in response.error.lower()
    
    @pytest.mark.asyncio
    async def test_mismatched_text_ids(self, tool):
        """Test error handling for mismatched text_ids length"""
        parameters = {
            "texts": ["Text one", "Text two"],
            "text_ids": ["id1"]  # Only one ID for two texts
        }
        
        response = await tool.execute(parameters)
        
        assert response.status == "error"
        assert "length must match" in response.error
    
    @pytest.mark.asyncio
    async def test_voice_analysis(self, tool):
        """Test voice analysis accuracy"""
        # Active voice
        active_params = {
            "text": "The doctor examined the patient.",
            "include_tokens": True
        }
        
        active_response = await tool.execute(active_params)
        assert active_response.status == "success"
        active_result = active_response.result
        
        # Passive voice
        passive_params = {
            "text": "The patient was examined by the doctor.",
            "include_tokens": True
        }
        
        passive_response = await tool.execute(passive_params)
        assert passive_response.status == "success"
        passive_result = passive_response.result
        
        # Check voice counts
        assert active_result["active_voice"] >= 1
        assert passive_result["passive_voice"] >= 1
        
        # Check detailed tokens
        active_tokens = active_result["detailed_tokens"]
        passive_tokens = passive_result["detailed_tokens"]
        
        assert len(active_tokens["active_voice_tokens"]) >= 1
        assert len(passive_tokens["passive_voice_tokens"]) >= 1
    
    @pytest.mark.asyncio
    async def test_readability_metrics(self, tool):
        """Test that readability metrics are calculated"""
        parameters = {
            "text": "This is a test sentence for readability analysis. It contains multiple sentences.",
            "include_tokens": False
        }
        
        response = await tool.execute(parameters)
        assert response.status == "success"
        result = response.result
        
        # Check readability scores are present
        readability_metrics = [
            "flesch_reading_ease",
            "flesch_kincaid_grade", 
            "automated_readability_index",
            "coleman_liau_index",
            "gunning_fog_index"
        ]
        
        for metric in readability_metrics:
            assert metric in result
            assert result[metric] is not None
    
    @pytest.mark.asyncio
    async def test_analysis_metadata(self, tool):
        """Test that analysis metadata is included"""
        parameters = {
            "text": "Sample text for metadata testing.",
            "include_tokens": False
        }
        
        response = await tool.execute(parameters)
        assert response.status == "success"
        result = response.result
        
        # Check metadata presence
        assert "analysis_metadata" in result
        metadata = result["analysis_metadata"]
        
        assert "text_length" in metadata
        assert "text_preview" in metadata
        assert "analysis_timestamp" in metadata
        assert "includes_detailed_tokens" in metadata
        
        # Check metadata values
        assert metadata["text_length"] > 0
        assert metadata["includes_detailed_tokens"] == False
        assert len(metadata["text_preview"]) > 0