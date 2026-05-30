from __future__ import annotations

import json
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .models import AgentAction, DocumentChunk, Ticket
from .rag import search_chunks


class MistralChatClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or settings.mistral_api_key
        self.base_url = base_url or settings.mistral_api_base_url
        self.model_name = model_name or settings.mistral_chat_model
        self.timeout = timeout

        if not self.api_key:
            raise RuntimeError(
                "MISTRAL_API_KEY is required to use the Mistral chat client."
            )

    async def generate(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        url = f"{self.base_url}/models/{self.model_name}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Mistral chat response did not contain any choices.")

        content = choices[0].get("message", {}).get("content")
        return content.strip() if isinstance(content, str) else ""


class ResolveAIAgent:
    """Autonomous ticket agent that enriches and resolves tickets with RAG context."""

    def __init__(
        self,
        model_name: str | None = None,
        temperature: float = 0.0,
        top_k: int = 3,
        client: MistralChatClient | None = None,
    ) -> None:
        self.client = client or MistralChatClient(model_name=model_name, timeout=settings.mistral_request_timeout)
        self.top_k = top_k
        self.temperature = temperature

    async def process_ticket(self, session: AsyncSession, ticket: Ticket) -> Ticket:
        """Process a ticket using retrieval-augmented generation and update the ticket state."""
        context_chunks = await search_chunks(session, ticket.description, top_k=self.top_k)
        context_text = self._build_context_text(context_chunks)
        prompt_messages = self._build_prompt(ticket, context_text)

        raw_response = await self.client.generate(messages=prompt_messages, temperature=self.temperature)
        parsed = self._parse_agent_response(raw_response)

        ticket.category = parsed.get("category") or ticket.category or "general"
        ticket.ai_response = parsed.get("ai_response")
        ticket.resolution_summary = parsed.get("resolution_summary")
        ticket.escalated = bool(parsed.get("escalated"))
        ticket.resolved = bool(parsed.get("resolved"))
        ticket.status = self._resolve_status(ticket)

        await self._log_action(
            session,
            ticket,
            tool_name="resolveai.agent",
            input_payload={
                "subject": ticket.subject,
                "description": ticket.description,
                "priority": ticket.priority,
                "context": context_text,
            },
            output_payload={"raw_response": raw_response, **parsed},
        )

        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)

        return ticket

    def _resolve_status(self, ticket: Ticket) -> str:
        if ticket.escalated:
            return "escalated"
        if ticket.resolved:
            return "resolved"
        return ticket.status or "open"

    def _build_context_text(self, chunks: list[DocumentChunk]) -> str:
        if not chunks:
            return "No knowledge base context was available for this ticket."

        context_sections = []
        for index, chunk in enumerate(chunks, start=1):
            source = getattr(chunk, "document", None)
            title = getattr(source, "title", None) if source is not None else None
            context_sections.append(
                f"Context #{index}: {title or 'document'}\n{chunk.chunk_text.strip()}"
            )
        return "\n\n".join(context_sections)

    def _build_prompt(self, ticket: Ticket, context_text: str) -> list[dict[str, str]]:
        system_prompt = (
            "You are ResolveAI, a support automation assistant. "
            "Read the ticket details and optional knowledge base context, then classify, answer, and summarize. "
            "Return valid JSON only."
        )

        user_prompt = (
            "Ticket details:\n"
            f"Subject: {ticket.subject}\n"
            f"Description: {ticket.description}\n"
            f"Priority: {ticket.priority}\n"
            f"Customer email: {ticket.customer_email}\n\n"
            "Knowledge base context:\n"
            f"{context_text}\n\n"
            "Produce a JSON object with the following fields:\n"
            "category, ai_response, resolution_summary, escalated, resolved, status.\n"
            "The response should be in the form:\n"
            "{\n"
            "  \"category\": \"...\",\n"
            "  \"ai_response\": \"...\",\n"
            "  \"resolution_summary\": \"...\",\n"
            "  \"escalated\": false,\n"
            "  \"resolved\": false,\n"
            "  \"status\": \"open\"\n"
            "}\n"
            "If the issue is likely self-resolvable, set resolved to true and status to resolved. "
            "If the ticket requires human attention, set escalated to true and status to escalated."
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _parse_agent_response(self, raw_response: str) -> dict[str, Any]:
        payload = self._extract_json(raw_response)
        if payload is None:
            return {
                "category": "general",
                "ai_response": raw_response.strip(),
                "resolution_summary": raw_response.strip(),
                "escalated": False,
                "resolved": False,
                "status": "open",
            }

        return {
            "category": payload.get("category", "general"),
            "ai_response": payload.get("ai_response") or payload.get("answer") or "",
            "resolution_summary": payload.get("resolution_summary") or payload.get("summary") or "",
            "escalated": bool(payload.get("escalated", False)),
            "resolved": bool(payload.get("resolved", False)),
            "status": payload.get("status", "open"),
        }

    def _extract_json(self, raw_text: str) -> dict[str, Any] | None:
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            first = raw_text.find("{")
            last = raw_text.rfind("}")
            if first != -1 and last != -1 and last > first:
                try:
                    return json.loads(raw_text[first : last + 1])
                except json.JSONDecodeError:
                    return None
            return None

    async def _log_action(
        self,
        session: AsyncSession,
        ticket: Ticket,
        tool_name: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
    ) -> None:
        action = AgentAction(
            ticket_id=ticket.id,
            tool_name=tool_name,
            input_payload=input_payload,
            output_payload=output_payload,
        )
        session.add(action)


# Expose a convenience function for external callers
async def run_agent_for_ticket(session: AsyncSession, ticket: Ticket) -> Ticket:
    agent = ResolveAIAgent()
    return await agent.process_ticket(session, ticket)
