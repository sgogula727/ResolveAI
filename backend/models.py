from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base() #declarative base for SQLAlchemy models


#main user ticket record
class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True) #primary key
    #descriptions
    created_at = Column(DateTime(timezone = True), default=datetime.utcnow) 
    updated_at = Column(DateTime(timezone = True), default=datetime.utcnow, onupdate=datetime.utcnow)
    #user information
    customer_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    #ai classficiation
    category = Column(String(80), nullable=True)
    status = Column(String(50), default="open")
    priority = Column(String(50), default="normal")
    #stores response text
    ai_response = Column(Text, nullable=True)
    escalated = Column(Boolean, default=False) #boolean
    resolved = Column(Boolean, default=False) #boolean
    resolution_summary = Column(Text, nullable=True) #final summary

    #one ticket can have many actions and metrics
    actions = relationship("AgentAction", back_populates="ticket", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="ticket", cascade="all, delete-orphan")

#full knowledge-base file 
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    source = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    doc_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    #allows to store orgiinla doc and link its chunks
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

#stores chucked texts and its embedding
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    #foreign key to Document
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    #actual text fragement
    chunk_text = Column(Text, nullable=False)
    #pgvector column
    embedding = Column(Vector(384), nullable=False) #change 384 to your embedding dimension
    #relationship back to document
    document = relationship("Document", back_populates="chunks")


#trakcs tool calls made by the agent, important for auditability and understanding agent behavior
class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    tool_name = Column(String(120), nullable=False)
    input_payload = Column(JSON, nullable=True)
    output_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="actions")

#stores ticket-level metrics
class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    name = Column(String(120), nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="metrics")

