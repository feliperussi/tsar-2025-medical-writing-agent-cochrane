"""
Tests for linguistic analysis API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app, register_tools
from api.core.tool_registry import tool_registry


class TestLinguisticAnalysisEndpoints:
    """Test class for linguistic analysis endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure tools are registered"""
        # Clear any existing tools and register fresh ones
        tool_registry._tools.clear()
        register_tools()
        self.client = TestClient(app)
    
    def test_basic_analysis_endpoint(self):
        """Test basic linguistic analysis endpoint"""
        response = self.client.post(
            "/tools/linguistic-analysis",
            json={
                "text": "The patient was treated by the doctor.",
                "include_tokens": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "analysis" in data
        analysis = data["analysis"]
        
        # Check required fields
        assert "words" in analysis
        assert "sentences" in analysis
        assert "passive_voice" in analysis
        assert "active_voice" in analysis
        assert "nouns" in analysis
        assert "verbs" in analysis
        
        # Check expected values for this text
        assert analysis["sentences"] == 1
        assert analysis["passive_voice"] >= 1  # "was treated"
        assert analysis["detailed_tokens"] is None  # Should be None when not requested
    
    def test_detailed_analysis_endpoint(self):
        """Test detailed linguistic analysis endpoint"""
        response = self.client.post(
            "/tools/linguistic-analysis/detailed",
            json={
                "text": "The patient was treated by the doctor."
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "analysis" in data
        analysis = data["analysis"]
        
        # Check that detailed tokens are included
        assert "detailed_tokens" in analysis
        detailed_tokens = analysis["detailed_tokens"]
        
        # Check token structure
        assert "passive_voice_tokens" in detailed_tokens
        assert "active_voice_tokens" in detailed_tokens
        assert "noun_tokens" in detailed_tokens
        assert "verb_tokens" in detailed_tokens
        
        # Check that passive voice tokens are present
        assert len(detailed_tokens["passive_voice_tokens"]) >= 1
    
    def test_multiple_texts_analysis(self):
        """Test multiple texts analysis endpoint"""
        response = self.client.post(
            "/tools/linguistic-analysis/multiple",
            json={
                "texts": [
                    "Simple sentence.",
                    "The complex medical intervention was successfully implemented."
                ],
                "text_ids": ["simple", "complex"],
                "include_tokens": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "analyses" in data
        assert "summary" in data
        
        analyses = data["analyses"]
        assert len(analyses) == 2
        
        # Check first analysis
        assert analyses[0]["text_id"] == "simple"
        assert analyses[0]["words"] == 2
        
        # Check second analysis
        assert analyses[1]["text_id"] == "complex"
        assert analyses[1]["words"] > analyses[0]["words"]  # More complex
        
        # Check summary
        summary = data["summary"]
        assert summary["total_texts"] == 2
        assert summary["includes_detailed_tokens"] == False
    
    def test_multiple_texts_with_tokens(self):
        """Test multiple texts analysis with detailed tokens"""
        response = self.client.post(
            "/tools/linguistic-analysis/multiple",
            json={
                "texts": [
                    "The doctor examined the patient.",
                    "The patient was examined by the doctor."
                ],
                "include_tokens": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        analyses = data["analyses"]
        assert len(analyses) == 2
        
        # Both should have detailed tokens
        for analysis in analyses:
            assert "detailed_tokens" in analysis
            assert "passive_voice_tokens" in analysis["detailed_tokens"]
            assert "active_voice_tokens" in analysis["detailed_tokens"]
        
        # First should be active voice, second passive
        assert len(analyses[0]["detailed_tokens"]["active_voice_tokens"]) >= 1
        assert len(analyses[1]["detailed_tokens"]["passive_voice_tokens"]) >= 1
    
    def test_empty_text_error(self):
        """Test error handling for empty text"""
        response = self.client.post(
            "/tools/linguistic-analysis",
            json={
                "text": "",
                "include_tokens": False
            }
        )
        
        assert response.status_code == 422  # Validation error for empty string
    
    def test_whitespace_only_text(self):
        """Test handling of whitespace-only text"""
        response = self.client.post(
            "/tools/linguistic-analysis",
            json={
                "text": "   ",
                "include_tokens": False
            }
        )
        
        assert response.status_code == 500  # Should return error for invalid text
        assert "empty" in response.json()["detail"].lower()
    
    def test_missing_text_parameter(self):
        """Test error when text parameter is missing"""
        response = self.client.post(
            "/tools/linguistic-analysis",
            json={
                "include_tokens": False
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_multiple_texts_empty_array(self):
        """Test error for empty texts array"""
        response = self.client.post(
            "/tools/linguistic-analysis/multiple",
            json={
                "texts": [],
                "include_tokens": False
            }
        )
        
        assert response.status_code == 422  # Validation error for empty array
    
    def test_multiple_texts_mismatched_ids(self):
        """Test error for mismatched text_ids length"""
        response = self.client.post(
            "/tools/linguistic-analysis/multiple",
            json={
                "texts": ["Text one", "Text two"],
                "text_ids": ["id1"],  # Only one ID for two texts
                "include_tokens": False
            }
        )
        
        assert response.status_code == 500
        assert "length must match" in response.json()["detail"]
    
    def test_readability_metrics_present(self):
        """Test that readability metrics are calculated"""
        response = self.client.post(
            "/tools/linguistic-analysis",
            json={
                "text": "This is a test sentence for readability analysis. It contains multiple sentences.",
                "include_tokens": False
            }
        )
        
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        
        # Check readability scores are present
        readability_metrics = [
            "flesch_reading_ease",
            "flesch_kincaid_grade", 
            "automated_readability_index",
            "coleman_liau_index",
            "gunning_fog_index"
        ]
        
        for metric in readability_metrics:
            assert metric in analysis
            assert analysis[metric] is not None
    
    def test_pos_distributions(self):
        """Test that POS distributions are calculated correctly"""
        response = self.client.post(
            "/tools/linguistic-analysis",
            json={
                "text": "The quick brown fox jumps over the lazy dog.",
                "include_tokens": False
            }
        )
        
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        
        # Check POS counts (spaCy may interpret some words differently)
        assert analysis["nouns"] >= 1  # at least fox or dog
        assert analysis["adjectives"] >= 2  # at least quick, brown, or lazy
        assert analysis["verbs"] >= 1  # jumps
        assert analysis["determiners"] >= 1  # at least one "the"
    
    def test_named_entity_recognition(self):
        """Test named entity recognition"""
        response = self.client.post(
            "/tools/linguistic-analysis",
            json={
                "text": "Dr. John Smith treated 5 patients at Mayo Clinic in 2023.",
                "include_tokens": True
            }
        )
        
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        
        # Check entity counts (may vary based on spaCy model)
        assert "person_entities" in analysis
        assert "organization_entities" in analysis
        assert "date_entities" in analysis
        assert "cardinal_entities" in analysis
        
        # Check detailed tokens for entities
        detailed = analysis["detailed_tokens"]
        # Should have some entity tokens
        total_entities = (
            len(detailed["person_entity_tokens"]) +
            len(detailed["organization_entity_tokens"]) +
            len(detailed["date_entity_tokens"]) +
            len(detailed["cardinal_entity_tokens"])
        )
        assert total_entities > 0
    
    def test_voice_analysis_accuracy(self):
        """Test accuracy of voice analysis"""
        # Test active voice
        response_active = self.client.post(
            "/tools/linguistic-analysis/detailed",
            json={"text": "The doctor examined the patient."}
        )
        
        # Test passive voice
        response_passive = self.client.post(
            "/tools/linguistic-analysis/detailed",
            json={"text": "The patient was examined by the doctor."}
        )
        
        assert response_active.status_code == 200
        assert response_passive.status_code == 200
        
        active_analysis = response_active.json()["analysis"]
        passive_analysis = response_passive.json()["analysis"]
        
        # Active voice sentence should have more active voice
        assert active_analysis["active_voice"] >= 1
        
        # Passive voice sentence should have more passive voice
        assert passive_analysis["passive_voice"] >= 1
        
        # Check token details
        active_tokens = active_analysis["detailed_tokens"]
        passive_tokens = passive_analysis["detailed_tokens"]
        
        assert len(active_tokens["active_voice_tokens"]) >= 1
        assert len(passive_tokens["passive_voice_tokens"]) >= 1
    
    def test_analysis_metadata(self):
        """Test that analysis metadata is included"""
        response = self.client.post(
            "/tools/linguistic-analysis",
            json={
                "text": "Sample text for metadata testing.",
                "include_tokens": False
            }
        )
        
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        
        # Check metadata presence
        assert "analysis_metadata" in analysis
        metadata = analysis["analysis_metadata"]
        
        assert "text_length" in metadata
        assert "text_preview" in metadata
        assert "analysis_timestamp" in metadata
        assert "includes_detailed_tokens" in metadata
        
        # Check metadata values
        assert metadata["text_length"] > 0
        assert metadata["includes_detailed_tokens"] == False
        assert len(metadata["text_preview"]) > 0