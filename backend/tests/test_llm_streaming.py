import asyncio
from typing import cast

from app.services.ai.llm_service import LLMClient


def test_chat_completion_stream_returns_incremental_chunks() -> None:
    client = LLMClient()

    async def fake_stream(messages, temperature=None, max_tokens=None):
        yield "你好"
        yield "，"
        yield "世界"

    client._call_with_fallback_stream = cast(object, fake_stream)

    async def run() -> list[str]:
        stream = await client.chat_completion(
            messages=[{"role": "user", "content": "你好"}],
            context_info={"assistant_intent": "general_chat"},
            stream=True,
        )
        chunks: list[str] = []
        async for chunk in stream:
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(run())

    assert chunks == ["你好", "，", "世界"]
