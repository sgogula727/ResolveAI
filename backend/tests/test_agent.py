import pytest

from backend.agent import MistralChatClient, ResolveAIAgent


class DummyClient:
    async def generate(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        return '{}'


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


def test_extract_json_valid_json() -> None:
    agent = ResolveAIAgent(client=DummyClient())
    raw = '{"category": "billing", "ai_response": "Here is the answer."}'

    parsed = agent._extract_json(raw)

    assert parsed == {
        "category": "billing",
        "ai_response": "Here is the answer.",
    }


def test_extract_json_invalid_json_returns_none() -> None:
    agent = ResolveAIAgent(client=DummyClient())
    raw = "This is not JSON"

    assert agent._extract_json(raw) is None


def test_parse_agent_response_falls_back_to_text() -> None:
    agent = ResolveAIAgent(client=DummyClient())
    raw = "I am not returning JSON. Here is a quick response."

    parsed = agent._parse_agent_response(raw)

    assert parsed["category"] == "general"
    assert "quick response" in parsed["ai_response"]
    assert parsed["resolved"] is False
    assert parsed["escalated"] is False


@pytest.mark.asyncio
async def test_build_context_text_without_chunks() -> None:
    agent = ResolveAIAgent(client=DummyClient())
    context = agent._build_context_text([])

    assert "No knowledge base context" in context


@pytest.mark.asyncio
async def test_mistral_chat_client_uses_chat_completions_endpoint(monkeypatch) -> None:
    calls = []

    class FakeAsyncClient:
        def __init__(self, timeout: int) -> None:
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, url: str, json: dict, headers: dict) -> FakeResponse:
            calls.append({"url": url, "json": json, "headers": headers})
            return FakeResponse({"choices": [{"message": {"content": "{}"}}]})

    monkeypatch.setattr("backend.agent.httpx.AsyncClient", FakeAsyncClient)

    client = MistralChatClient(
        api_key="test-key",
        base_url="https://api.mistral.ai/v1/",
        model_name="mistral-small-latest",
    )
    result = await client.generate([{"role": "user", "content": "Hello"}])

    assert result == "{}"
    assert calls[0]["url"] == "https://api.mistral.ai/v1/chat/completions"
    assert calls[0]["json"]["model"] == "mistral-small-latest"
    assert calls[0]["json"]["response_format"] == {"type": "json_object"}
