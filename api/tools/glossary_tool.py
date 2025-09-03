from typing import Dict, Any
from api.core.base_tool import BaseTool
from api.schemas.base import ToolInfo, ToolResponse
from api.schemas.glossary import GlossaryDefinition
from api.core.glossary_singleton import glossary_singleton

class GlossaryTool(BaseTool):
    """Tool for finding and defining medical phrases in text"""
    
    def __init__(self):
        self.glossary_service = glossary_singleton.get_service()
    
    @property
    def info(self) -> ToolInfo:
        return ToolInfo(
            name="glossary",
            description="Find and define complex medical phrases within a body of text with location information",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to analyze for medical terms"
                    }
                },
                "required": ["text"]
            },
            version="2.0.0"
        )
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResponse:
        if not self.glossary_service:
            return ToolResponse(
                tool_name="glossary",
                status="error",
                error="Glossary service is not available"
            )
        
        if not self.validate_parameters(parameters):
            return ToolResponse(
                tool_name="glossary",
                status="error",
                error="Missing required parameter: text"
            )
        
        text = parameters.get("text")
        
        try:
            # Always use the enhanced method
            result = self.glossary_service.find_and_define_phrases_in_text_enhanced(text)
            return ToolResponse(
                tool_name="glossary",
                status="success",
                result=result
            )
        except Exception as e:
            return ToolResponse(
                tool_name="glossary",
                status="error",
                error=str(e)
            )