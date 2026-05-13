"""
MCP tool decorator and tool registry.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol
import json



@dataclass
class ToolSchema:
    """
    MCP tool schema. Can check OpenAI documentation for details: https://platform.openai.com/docs/guides/function-calling?api-mode=chat#defining-functions
    Parameters:
        name: tool name
        description: tool description
        input_schema: tool input schema
    """

    name: str
    description: str
    input_schema: Dict[str, Any]
    type: str = "function"


def mcp_tool(input_schema: Dict[str, Any], description: str = ""):
    """
    Decorator to mark a method as an MCP tool. Tells the LLM what tools are available (tool name) and how to use them (tool input schema).

    Example：

    @mcp_tool(
        input_schema={...},
        description="Explain what this tool does."
    )
    def my_tool(self, ...):
        ...

    """

    def decorator(func: Callable) -> Callable:
        schema = ToolSchema(
            name=func.__name__,
            description=description or (func.__doc__ or "").strip(),
            input_schema=input_schema or {},
        )
        # 标记为 MCP 工具
        setattr(func, "_is_mcp_tool", True)
        setattr(func, "_mcp_tool_schema", schema)
        return func

    return decorator


class ToolRegistry:
    """
    Tool registry. Register tools and their schemas, and call tools.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, ToolSchema] = {}

    def register_tool(self, name: str, func: Callable, schema: ToolSchema) -> None:
        """
        Register a tool to the registry.
        """

        self._tools[name] = func
        self._schemas[name] = schema

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool by name with given arguments.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")

        func = self._tools[name]
                
        return func(**(arguments or {}))
