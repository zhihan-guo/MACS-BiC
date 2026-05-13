"""
LLM client, where you call the API to generate response
"""
import openai
from openai import OpenAI

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

import requests

class LLMClient:
    """ A demo class """

    def __init__(self, api_key: str, model_name: str = "gpt-4o-2024-11-20", base_url: str = "https://az.gptplus5.com/v1"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def generate(
        self,
        hist_messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call the API to generate response.

        Parameters:
            hist_messages: history conversation messages (for example OpenAI format, see: https://platform.openai.com/docs/api-reference/chat )：
                [
                    {
                        "role": "user",
                        "content": "Hello, how are you?"
                    },
                    {
                        "role": "assistant",
                        "content": "I'm good, thank you!"
                    }
                ]
            tools: tool schema list, optional.
            kwargs: keyword arguments for the API. (for example, temperature, max_tokens, etc.)

        Returns:
            response: response from the API (parsed JSON).
        """
        if kwargs is None:
            kwargs = {}
            
        # response = requests.post(
        #     url=f"{self.base_url}/chat/completions",
        #     headers={
        #         "Authorization": f"Bearer {self.api_key}",
        #     },
        #     json={
        #         "model": self.model_name,
        #         "messages": hist_messages,
        #         "tools": tools,
        #         **kwargs,
        #     },
        # )
        client = OpenAI(
            base_url = self.base_url,
            api_key = self.api_key
        )
        response = client.chat.completions.create(
            model = self.model_name,
            messages = hist_messages,
            tools = tools,
        )
        # result = response.json()
        message = response.choices[0].message
        return message
