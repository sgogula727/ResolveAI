from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class TicketCreate(BaseModel):
    customer_email: EmailStr
    subject: str
    description: str
    priority: Optional[str] = Field("normal", description="Ticket priority")


class TicketUpdate(BaseModel):
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    ai_response: Optional[str] = None
    escalated: Optional[bool] = None
    resolved: Optional[bool] = None
    resolution_summary: Optional[str] = None


class TicketResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    customer_email: EmailStr
    subject: str
    description: str
    category: Optional[str]
    status: str
    priority: str
    ai_response: Optional[str]
    escalated: bool
    resolved: bool
    resolution_summary: Optional[str]

    class Config:
        orm_mode = True


class DocumentCreate(BaseModel):
    title: str
    source: Optional[str] = None
    content: str
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    id: int
    title: str
    source: Optional[str]
    content: str
    doc_metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        orm_mode = True


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_text: str

    class Config:
        orm_mode = True


class AgentActionResponse(BaseModel):
    id: int
    ticket_id: int
    tool_name: str
    input_payload: Optional[Dict[str, Any]]
    output_payload: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        orm_mode = True


class MetricResponse(BaseModel):
    id: int
    ticket_id: int
    name: str
    value: float
    created_at: datetime

    class Config:
        orm_mode = True
