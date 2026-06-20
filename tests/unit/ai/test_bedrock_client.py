from __future__ import annotations

import io
import json

from todo_app.contexts.ai.container import _build_llm_client
from todo_app.contexts.ai.domain.value_objects.model_identifier import ModelIdentifier
from todo_app.contexts.ai.domain.value_objects.prompt_text import PromptText
from todo_app.contexts.ai.infrastructure.bedrock.bedrock_client import BedrockLlmClient
from todo_app.contexts.ai.infrastructure.bedrock.stub_client import StubLlmClient


class _FakeBedrock:
    def invoke_model(self, *, modelId, body, contentType, accept):  # noqa: N803
        payload = {"content": [{"text": "Focus on the urgent task."}]}
        return {"body": io.BytesIO(json.dumps(payload).encode())}


async def test_bedrock_client_parses_completion():
    client = BedrockLlmClient(region="us-east-1", client=_FakeBedrock())
    result = await client.complete(PromptText("hi"), ModelIdentifier("m"))
    assert result.text == "Focus on the urgent task."
    assert result.model == "m"


def test_build_llm_client_selects_impl():
    assert isinstance(_build_llm_client(debug=True, region="us-east-1"), StubLlmClient)
    assert isinstance(_build_llm_client(debug=False, region="us-east-1"), BedrockLlmClient)


async def test_stub_client_returns_deterministic_text():
    out = await StubLlmClient().complete(PromptText("plan my day"), ModelIdentifier("m"))
    assert "stub:m" in out.text
