from pydantic import BaseModel
from typing import Dict, Any, Optional

class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class ToolResponse(BaseModel):
    tool_name: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None

class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    version: str = "1.0.0"