from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .agent import run_agent_for_ticket
from .db import get_session, init_db
from .models import Document, Ticket
from .rag import create_document, get_document_chunks
from .schemas import (
    AgentActionResponse,
    DocumentCreate,
    DocumentChunkResponse,
    DocumentResponse,
    MetricResponse,
    TicketCreate,
    TicketResponse,
    TicketUpdate,
)
from .tools import save_upload_file

app = FastAPI(title="ResolveAI Backend", version="0.1.0")

@app.on_event("startup")
async def startup_event() -> None:
    await init_db()

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "ResolveAI Backend"}

@app.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    payload: TicketCreate,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    ticket = Ticket(
        customer_email=payload.customer_email,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)

    try:
        ticket = await run_agent_for_ticket(session, ticket)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ticket created but agent processing failed: {exc}",
        )

    return ticket

@app.post("/tickets/{ticket_id}/process", response_model=TicketResponse)
async def process_ticket(
    ticket_id: int,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        ticket = await run_agent_for_ticket(session, ticket)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent processing failed: {exc}",
        )

    return ticket

@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.get("/tickets", response_model=list[TicketResponse])
async def list_tickets(session: AsyncSession = Depends(get_session)) -> list[TicketResponse]:
    result = await session.execute(select(Ticket).order_by(Ticket.created_at.desc()))
    return result.scalars().all()

@app.patch("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket

@app.get("/tickets/{ticket_id}/actions", response_model=list[AgentActionResponse])
async def list_ticket_actions(
    ticket_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[AgentActionResponse]:
    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket.actions

@app.get("/tickets/{ticket_id}/metrics", response_model=list[MetricResponse])
async def list_ticket_metrics(
    ticket_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[MetricResponse]:
    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket.metrics

@app.post("/documents", response_model=DocumentResponse)
async def create_document_endpoint(
    payload: DocumentCreate,
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    document = await create_document(
        session,
        title=payload.title,
        source=payload.source or "manual",
        content=payload.content,
        metadata=payload.metadata,
    )
    return document

@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    payload = await file.read()
    save_upload_file(file.filename, payload)
    content = payload.decode("utf-8", errors="replace")
    document = await create_document(
        session,
        title=file.filename,
        source="upload",
        content=content,
        metadata={"filename": file.filename},
    )
    return document

@app.get("/documents", response_model=list[DocumentResponse])
async def list_documents(session: AsyncSession = Depends(get_session)) -> list[DocumentResponse]:
    result = await session.execute(select(Document).order_by(Document.created_at.desc()))
    return result.scalars().all()

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, session: AsyncSession = Depends(get_session)) -> DocumentResponse:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.get("/documents/{document_id}/chunks", response_model=list[DocumentChunkResponse])
async def get_document_chunks_endpoint(
    document_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[DocumentChunkResponse]:
    chunks = await get_document_chunks(session, document_id)
    return chunks