from typing import Dict, List, Optional
from api.core.base_tool import BaseTool
from api.schemas.base import ToolInfo


class ToolRegistry:
    """Registry for managing available tools"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """Register a new tool"""
        tool_info = tool.info
        self._tools[tool_info.name] = tool
        print(f"Registered tool: {tool_info.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[ToolInfo]:
        """List all registered tools"""
        return [tool.info for tool in self._tools.values()]
    
    def tool_exists(self, name: str) -> bool:
        """Check if a tool exists"""
        return name in self._tools


# Global registry instance
tool_registry = ToolRegistry()