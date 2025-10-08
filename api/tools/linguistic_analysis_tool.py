"""
Linguistic Analysis Tool for the Medical Writing API
Provides comprehensive text analysis including readability scores, 
POS distributions, entity recognition, and stylistic metrics.
"""

from typing import Dict, Any, List, Optional
from api.core.base_tool import BaseTool
from api.schemas.base import ToolInfo, ToolResponse
from api.utils.text_analyzer import TextLinguisticAnalyzer


class LinguisticAnalysisTool(BaseTool):
    """Tool for comprehensive linguistic analysis of medical texts"""
    
    def __init__(self):
        """Initialize the linguistic analysis tool"""
        self._analyzer = None
    
    @property
    def analyzer(self) -> TextLinguisticAnalyzer:
        """Lazy loading of the analyzer to avoid loading spaCy model at import time"""
        if self._analyzer is None:
            self._analyzer = TextLinguisticAnalyzer()
        return self._analyzer
    
    @property
    def info(self) -> ToolInfo:
        """Return tool information"""
        return ToolInfo(
            name="linguistic_analysis",
            description="Comprehensive linguistic analysis of text including readability scores, POS distributions, named entity recognition, and stylistic metrics",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to analyze"
                    },
                    "texts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of texts to analyze (alternative to single text)"
                    },
                    "text_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional IDs for each text when analyzing multiple texts"
                    },
                    "include_tokens": {
                        "type": "boolean",
                        "description": "Whether to include detailed token information for each linguistic category",
                        "default": False
                    }
                },
                "required": [],
                "oneOf": [
                    {"required": ["text"]},
                    {"required": ["texts"]}
                ]
            },
            version="1.0.0"
        )
    
    def _simplify_tokens(self, detailed_tokens: Dict[str, List]) -> Dict[str, List[str]]:
        """Convert detailed token objects to unique word lists"""
        simplified = {}
        for key, tokens in detailed_tokens.items():
            if isinstance(tokens, list) and tokens:
                # Extract unique text values from token objects
                unique_words = set()
                for token in tokens:
                    if isinstance(token, dict) and "text" in token:
                        unique_words.add(token["text"])
                # Only include non-empty categories
                if unique_words:
                    simplified[key] = sorted(list(unique_words))
        return simplified
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResponse:
        """Execute linguistic analysis"""
        try:
            # Validate parameters
            text = parameters.get("text")
            texts = parameters.get("texts")
            text_ids = parameters.get("text_ids")
            include_tokens = parameters.get("include_tokens", False)
            simplify_tokens = parameters.get("simplify_tokens", False)
            
            if not text and not texts:
                return ToolResponse(
                    tool_name="linguistic_analysis",
                    status="error",
                    error="Either 'text' or 'texts' parameter is required"
                )
            
            # Single text analysis
            if text:
                result = self.analyzer.analyze_text(text, include_tokens=include_tokens)
                
                if "error" in result:
                    return ToolResponse(
                        tool_name="linguistic_analysis",
                        status="error",
                        error=result["error"]
                    )
                
                # Optionally include simplified word lists and omit detailed objects
                if include_tokens and simplify_tokens and "detailed_tokens" in result:
                    result["simplified_tokens"] = self._simplify_tokens(result["detailed_tokens"])
                    result["detailed_tokens"] = None
                
                return ToolResponse(
                    tool_name="linguistic_analysis",
                    status="success",
                    result=result
                )
            
            # Multiple texts analysis
            if texts:
                if not isinstance(texts, list):
                    return ToolResponse(
                        tool_name="linguistic_analysis",
                        status="error",
                        error="'texts' parameter must be an array of strings"
                    )
                
                if text_ids and len(text_ids) != len(texts):
                    return ToolResponse(
                        tool_name="linguistic_analysis",
                        status="error",
                        error="'text_ids' length must match 'texts' length"
                    )
                
                results = self.analyzer.analyze_multiple_texts(
                    texts, 
                    text_ids=text_ids, 
                    include_tokens=include_tokens
                )
                
                # Check for errors and simplify tokens in each result
                for result in results:
                    if "error" in result:
                        return ToolResponse(
                            tool_name="linguistic_analysis",
                            status="error",
                            error=f"Analysis failed for text '{result.get('text_id', 'unknown')}': {result['error']}"
                        )
                    
                    # Optionally include simplified word lists and omit detailed objects
                    if include_tokens and simplify_tokens and "detailed_tokens" in result:
                        result["simplified_tokens"] = self._simplify_tokens(result["detailed_tokens"])
                        result["detailed_tokens"] = None
                
                return ToolResponse(
                    tool_name="linguistic_analysis",
                    status="success",
                    result={
                        "analyses": results,
                        "summary": {
                            "total_texts": len(results),
                            "includes_detailed_tokens": include_tokens
                        }
                    }
                )
                
        except Exception as e:
            return ToolResponse(
                tool_name="linguistic_analysis",
                status="error",
                error=f"Linguistic analysis failed: {str(e)}"
            )