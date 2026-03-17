# -*- coding: utf-8 -*-
"""Modelos do serviço de tickets de suporte."""
from __future__ import annotations

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Ticket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    created_by = Column(String(36), nullable=False)          # user_id
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SAEnum(TicketStatus), default=TicketStatus.OPEN, nullable=False)
    priority = Column(SAEnum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)
    category = Column(String(50), nullable=False, default="general")
    assigned_to = Column(String(36), nullable=True)          # admin user_id
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(String(36), nullable=False)
    author_role = Column(String(20), nullable=False, default="client")  # "client" | "admin"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
