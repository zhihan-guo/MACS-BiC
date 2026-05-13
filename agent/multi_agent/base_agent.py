"""
Base agent, where you can implement the ReAct loop.
"""


from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from .llm_client import LLMClient
from .mcp_tool import ToolRegistry, mcp_tool

import json

class ReActBaseAgent:
    """
    ReAct base agent. The agent works iteratively, in each round:
    1. call the LLM to generate response
    2. parse the response to get the tool calls
    3. execute the tool calls
    4. write the tool results back to the conversation history
    5. continue the next round until the task is finished or the maximum number of iterations is reached    
    """

    def __init__(self, llm_client: LLMClient, system_prompt: str) -> None:
        self.llm = llm_client
        self.system_prompt = system_prompt
        self.conversation_history: List[Dict[str, Any]] = []
        self.iteration_count: int = 0
        self.max_iterations: int = 10
        self.tool_registry = ToolRegistry()
        # Register all MCP tools from this instance
        self._register_builtin_tools()
        # Build tool schemas for LLM
        self.tool_schemas = self._build_tool_schemas()

    def execute_task(self, task_input: str) -> Dict[str, Any]:
        """
        Parameters:
            task_input: user task input (e.g., "Search the web for the latest news about the stock market")

        Return task execution result.
        """
        self.conversation_history.append({"role": "system", "content": self.system_prompt})
        self.conversation_history.append({"role": "user", "content": task_input})

        for _ in range(self.max_iterations):
            response = self.llm.generate(
                hist_messages=self.conversation_history,
                tools=self.tool_schemas,
            )

            # append the response to the conversation history
            if response.content is None:
                self.conversation_history.append({"role": "assistant", "content": ""})
            else:
                self.conversation_history.append({"role": "assistant", "content": response.content})

            # extract tool calls if any
            extracted_tool_calls = []
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    function = tool_call.function
                    tool_name = function.name
                    arguments = json.loads(function.arguments)
                    extracted_tool_calls.append({"name": tool_name, "arguments": arguments})

            # execute the tool calls, check OpenAI response format (https://platform.openai.com/docs/guides/function-calling?api-mode=chat)
            for tool_call in extracted_tool_calls:
                tool_result = self.execute_tool_call(tool_call)
                # Convert tool result to string for conversation history
                if isinstance(tool_result, dict):
                    tool_result_str = str(tool_result)
                else:
                    tool_result_str = str(tool_result)
                self.conversation_history.append({"role": "tool", "content": tool_result_str})
                
                # check if the task is finished (task_done tool was called)
                if tool_call.get("name") == "task_done":
                    if isinstance(tool_result, dict) and tool_result.get("success"):
                        return {"success": True, "data": tool_result.get("data")}

        return {"success": False, "data": "Task failed to complete within the maximum number of iterations."}

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "task_done_summary": {
                    "type": "string",
                    "description": "Your summary about the task execution result"
                }
            },
            "required": ["task_done_summary"]
        },
        description="Mark the task as done. Call this when you have completed the task."
    )
    def task_done(self, task_done_summary: str) -> Dict[str, Any]:
        """
        Mark the task as done.
        Parameters:
            task_done_summary: your summary about the task execution result
        """
        return {"success": True, "data": task_done_summary}


    def _register_builtin_tools(self) -> None:
        """
        Automatically scan and register all methods marked with @mcp_tool decorator.
        """
        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue
            attr = getattr(self, attr_name)
            if not callable(attr):
                continue
            # Check if this method is marked as MCP tool
            if hasattr(attr, "_is_mcp_tool") and hasattr(attr, "_mcp_tool_schema"):
                schema = getattr(attr, "_mcp_tool_schema")
                # Bind the method to self instance
                bound_method = attr.__get__(self, type(self))
                self.tool_registry.register_tool(schema.name, bound_method, schema)

    def _build_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Build tool schemas in OpenAI format for LLM.
        Returns a list of tool definitions that can be passed to LLM API.
        """
        schemas = []
        for schema in self.tool_registry._schemas.values():
            # Convert to OpenAI function calling format
            tool_def = {
                "type": "function",
                "function": {
                    "name": schema.name,
                    "description": schema.description,
                    "parameters": schema.input_schema
                }
            }
            schemas.append(tool_def)
        return schemas

    def execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call.
        Parameters:
            tool_call: tool call dictionary with "name" and "arguments" keys
        """
        tool_name = tool_call.get('name')
        arguments = tool_call.get('arguments')
        return self.tool_registry.call_tool(tool_name, arguments)
