"""Bedrock adapter implementing LlmClient — the ONLY module aware the LLM is AWS Bedrock."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from todo_app.contexts.ai.domain.ports.llm_client import LlmClient, LlmCompletion

if TYPE_CHECKING:
    from todo_app.contexts.ai.domain.value_objects.model_identifier import ModelIdentifier
    from todo_app.contexts.ai.domain.value_objects.prompt_text import PromptText


class BedrockLlmClient(LlmClient):
    def __init__(self, *, region: str, max_tokens: int = 512, client=None) -> None:
        self._region = region
        self._max_tokens = max_tokens
        self._client = client

    def _get_client(self):
        if self._client is None:  # pragma: no cover - exercised only with real AWS
            import boto3

            self._client = boto3.client("bedrock-runtime", region_name=self._region)
        return self._client

    async def complete(self, prompt: PromptText, model: ModelIdentifier) -> LlmCompletion:
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self._max_tokens,
                "messages": [{"role": "user", "content": str(prompt)}],
            }
        )
        response = await asyncio.to_thread(
            self._get_client().invoke_model,
            modelId=str(model),
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(response["body"].read())
        text = "".join(block.get("text", "") for block in payload.get("content", []))
        return LlmCompletion(text=text.strip(), model=str(model))
