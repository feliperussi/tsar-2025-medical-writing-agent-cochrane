from abc import ABC, abstractmethod
from typing import Dict, Any
from api.schemas.base import ToolInfo, ToolResponse


class BaseTool(ABC):
    """Abstract base class for all tools"""
    
    @property
    @abstractmethod
    def info(self) -> ToolInfo:
        """Return tool information including name, description, and parameters"""
        pass
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResponse:
        """Execute the tool with given parameters"""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate that required parameters are present"""
        required_params = self.info.parameters.get("required", [])
        return all(param in parameters for param in required_params)