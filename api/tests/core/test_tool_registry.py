import pytest
from api.core.tool_registry import ToolRegistry
from api.core.base_tool import BaseTool
from api.schemas.base import ToolInfo, ToolResponse
from typing import Dict, Any


class MockTool(BaseTool):
    """Mock tool for testing"""
    
    def __init__(self, name: str = "mock_tool"):
        self._name = name
    
    @property
    def info(self) -> ToolInfo:
        return ToolInfo(
            name=self._name,
            description="A mock tool for testing",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            },
            version="1.0.0"
        )
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResponse:
        return ToolResponse(
            tool_name=self._name,
            status="success",
            result={"echo": parameters.get("input", "")}
        )


class TestToolRegistry:
    """Test the ToolRegistry class"""
    
    def test_register_tool(self):
        """Test registering a new tool"""
        registry = ToolRegistry()
        tool = MockTool()
        
        registry.register(tool)
        
        assert registry.tool_exists("mock_tool")
        assert len(registry._tools) == 1
    
    def test_register_multiple_tools(self):
        """Test registering multiple tools"""
        registry = ToolRegistry()
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")
        
        registry.register(tool1)
        registry.register(tool2)
        
        assert registry.tool_exists("tool1")
        assert registry.tool_exists("tool2")
        assert len(registry._tools) == 2
    
    def test_get_tool(self):
        """Test retrieving a registered tool"""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        
        retrieved_tool = registry.get_tool("mock_tool")
        
        assert retrieved_tool is not None
        assert retrieved_tool.info.name == "mock_tool"
    
    def test_get_nonexistent_tool(self):
        """Test retrieving a non-existent tool"""
        registry = ToolRegistry()
        
        tool = registry.get_tool("nonexistent")
        
        assert tool is None
    
    def test_list_tools(self):
        """Test listing all registered tools"""
        registry = ToolRegistry()
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")
        
        registry.register(tool1)
        registry.register(tool2)
        
        tools = registry.list_tools()
        
        assert len(tools) == 2
        assert all(isinstance(tool, ToolInfo) for tool in tools)
        
        tool_names = [tool.name for tool in tools]
        assert "tool1" in tool_names
        assert "tool2" in tool_names
    
    def test_list_tools_empty_registry(self):
        """Test listing tools when registry is empty"""
        registry = ToolRegistry()
        
        tools = registry.list_tools()
        
        assert tools == []
    
    def test_tool_exists(self):
        """Test checking if a tool exists"""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        
        assert registry.tool_exists("mock_tool") is True
        assert registry.tool_exists("nonexistent") is False
    
    def test_register_overwrites_existing(self):
        """Test that registering a tool with same name overwrites existing"""
        registry = ToolRegistry()
        tool1 = MockTool("same_name")
        tool2 = MockTool("same_name")
        
        registry.register(tool1)
        registry.register(tool2)
        
        assert len(registry._tools) == 1
        assert registry.get_tool("same_name") is tool2