import pytest

from backend.agent import ResolveAIAgent


class DummyClient:
    async def generate(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        return '{}'


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
