import pytest
from fastapi import status


def test_root_endpoint(client):
    """Test the root endpoint returns API information"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert "message" in data
    assert data["message"] == "Medical Writing Tools API"
    assert "available_tools" in data
    assert "glossary" in data["available_tools"]
    assert "endpoints" in data


def test_list_tools_endpoint(client):
    """Test the list tools endpoint"""
    response = client.get("/tools/list")
    assert response.status_code == status.HTTP_200_OK
    
    tools = response.json()
    assert isinstance(tools, list)
    assert len(tools) > 0
    
    # Check glossary tool is present
    glossary_tool = next((t for t in tools if t["name"] == "glossary"), None)
    assert glossary_tool is not None
    assert glossary_tool["description"] == "Find and define complex medical phrases within a body of text with location information"
    assert "parameters" in glossary_tool
    assert glossary_tool["version"] == "2.0.0"


def test_glossary_endpoint_success(client, sample_medical_text):
    """Test the glossary endpoint with valid input"""
    response = client.post(
        "/tools/glossary",
        json={"text": sample_medical_text}
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "analysis_summary" in data
    assert "found_terms" in data
    
    summary = data["analysis_summary"]
    assert summary["total_unique_phrases_found"] > 0
    
    # Check that known phrases were found
    found_main_terms = [term["main_term"].lower() for term in data["found_terms"]]
    assert any("adverse effects" in term for term in found_main_terms)
    assert any("clinical trial" in term for term in found_main_terms)
    assert any("diabetes" in term for term in found_main_terms)


def test_glossary_endpoint_empty_text(client):
    """Test glossary endpoint with empty text"""
    response = client.post(
        "/tools/glossary",
        json={"text": ""}
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["analysis_summary"]["total_unique_phrases_found"] == 0
    assert len(data["found_terms"]) == 0


def test_glossary_endpoint_missing_text(client):
    """Test glossary endpoint with missing text field"""
    response = client.post(
        "/tools/glossary",
        json={}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_generic_tools_endpoint_success(client, sample_medical_text):
    """Test the generic tools endpoint with glossary tool"""
    response = client.post(
        "/tools",
        json={
            "tool_name": "glossary",
            "parameters": {"text": sample_medical_text}
        }
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["tool_name"] == "glossary"
    assert data["status"] == "success"
    assert data["result"] is not None
    assert "analysis_summary" in data["result"]
    assert "found_terms" in data["result"]
    assert data["result"]["analysis_summary"]["total_unique_phrases_found"] > 0


def test_generic_tools_endpoint_unknown_tool(client):
    """Test generic tools endpoint with unknown tool"""
    response = client.post(
        "/tools",
        json={
            "tool_name": "unknown_tool",
            "parameters": {"text": "test"}
        }
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["tool_name"] == "unknown_tool"
    assert data["status"] == "error"
    assert "Unknown tool" in data["error"]


def test_generic_tools_endpoint_missing_parameters(client):
    """Test generic tools endpoint with missing parameters"""
    response = client.post(
        "/tools",
        json={
            "tool_name": "glossary",
            "parameters": {}
        }
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["status"] == "error"
    assert "Missing required parameter" in data["error"]


def test_glossary_response_structure(client, sample_medical_text_with_hypertension):
    """Test the structure of glossary response"""
    response = client.post(
        "/tools/glossary",
        json={"text": sample_medical_text_with_hypertension}
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    
    # Check overall structure
    assert "analysis_summary" in data
    assert "found_terms" in data
    
    # Find hypertension in found_terms
    hypertension_term = None
    for term in data["found_terms"]:
        if "hypertension" in term["main_term"].lower():
            hypertension_term = term
            break
    
    assert hypertension_term is not None
    assert "definitions" in hypertension_term
    assert "matches_in_text" in hypertension_term
    
    # Check definition structure
    for definition in hypertension_term["definitions"]:
        assert "plain_alternative" in definition
        assert "source" in definition
        assert isinstance(definition["plain_alternative"], str)
        assert isinstance(definition["source"], str)


def test_glossary_endpoint_location_info(client, sample_medical_text):
    """Test the glossary endpoint includes location information"""
    response = client.post(
        "/tools/glossary",
        json={"text": sample_medical_text}
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    
    # Check overall structure
    assert "analysis_summary" in data
    assert "found_terms" in data
    
    # Check analysis summary
    summary = data["analysis_summary"]
    assert "total_unique_phrases_found" in summary
    assert "text_character_length" in summary
    assert summary["text_character_length"] == len(sample_medical_text)
    
    # Check found terms structure
    found_terms = data["found_terms"]
    assert isinstance(found_terms, list)
    assert len(found_terms) > 0
    
    # Check first term structure
    term = found_terms[0]
    assert "main_term" in term
    assert "definitions" in term
    assert "matches_in_text" in term
    
    # Check definitions structure
    definitions = term["definitions"]
    assert isinstance(definitions, list)
    assert len(definitions) > 0
    
    for definition in definitions:
        assert "plain_alternative" in definition
        assert "source" in definition
    
    # Check matches structure
    matches = term["matches_in_text"]
    assert isinstance(matches, list)
    assert len(matches) > 0
    
    for match in matches:
        assert "alias_found" in match
        assert "location_start" in match
        assert "location_end" in match
        assert isinstance(match["location_start"], int)
        assert isinstance(match["location_end"], int)
        assert match["location_start"] < match["location_end"]


def test_glossary_via_generic_endpoint_with_locations(client):
    """Test glossary via generic tools endpoint returns location info"""
    response = client.post(
        "/tools",
        json={
            "tool_name": "glossary",
            "parameters": {
                "text": "The patient has diabetes."
            }
        }
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["tool_name"] == "glossary"
    assert data["status"] == "success"
    
    result = data["result"]
    assert "analysis_summary" in result
    assert "found_terms" in result
    
    # Should find diabetes
    found_terms = result["found_terms"]
    diabetes_found = any(
        "diabetes" in term["main_term"].lower() 
        for term in found_terms
    )
    assert diabetes_found


def test_glossary_location_accuracy(client):
    """Test that location information is accurate"""
    text = "Patient has diabetes and hypertension"
    response = client.post(
        "/tools/glossary",
        json={"text": text}
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    found_terms = data["found_terms"]
    
    # Verify that extracted text matches original
    for term in found_terms:
        for match in term["matches_in_text"]:
            start = match["location_start"]
            end = match["location_end"]
            extracted_text = text[start:end]
            assert extracted_text.lower() == match["alias_found"].lower()