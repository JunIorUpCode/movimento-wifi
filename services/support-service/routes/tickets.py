# -*- coding: utf-8 -*-
"""Endpoints REST do serviço de tickets de suporte."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..models.ticket import TicketStatus, TicketPriority
from ..services.ticket_service import TicketService

router = APIRouter(prefix="/api/tickets", tags=["tickets"])
_svc = TicketService()


# ── Schemas ───────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str = Field(default="general", max_length=50)


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    resolution: Optional[str] = None


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class TicketOut(BaseModel):
    id: int
    tenant_id: str
    created_by: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: str
    assigned_to: Optional[str]
    resolution: Optional[str]
    created_at: str
    updated_at: Optional[str]
    resolved_at: Optional[str]

    model_config = {"from_attributes": True}


class CommentOut(BaseModel):
    id: int
    ticket_id: int
    author_id: str
    author_role: str
    content: str
    created_at: str

    model_config = {"from_attributes": True}


# ── Helpers (mock — em produção vêm do JWT) ───────────────────────────────────

def _get_tenant_id(x_tenant_id: str = Query(...)) -> str:
    return x_tenant_id


def _get_user_id(x_user_id: str = Query(...)) -> str:
    return x_user_id


def _get_db() -> Session:  # pragma: no cover
    """Substitua pelo DB real via dependency injection."""
    raise NotImplementedError


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(
    body: TicketCreate,
    tenant_id: str = Depends(_get_tenant_id),
    user_id: str = Depends(_get_user_id),
    db: Session = Depends(_get_db),
):
    """Abre um novo ticket de suporte."""
    ticket = _svc.create(
        db, tenant_id=tenant_id, created_by=user_id,
        title=body.title, description=body.description,
        priority=body.priority, category=body.category,
    )
    return _ticket_to_out(ticket)


@router.get("", response_model=list[TicketOut])
def list_tickets(
    status: Optional[TicketStatus] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    tenant_id: str = Depends(_get_tenant_id),
    db: Session = Depends(_get_db),
):
    """Lista tickets do tenant autenticado."""
    tickets = _svc.list_by_tenant(db, tenant_id=tenant_id, status=status, limit=limit, offset=offset)
    return [_ticket_to_out(t) for t in tickets]


@router.get("/admin", response_model=list[TicketOut])
def list_all_tickets(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: Session = Depends(_get_db),
):
    """Lista todos os tickets — somente admins."""
    tickets = _svc.list_all(db, status=status, priority=priority, limit=limit, offset=offset)
    return [_ticket_to_out(t) for t in tickets]


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(_get_db)):
    t = _svc.get(db, ticket_id)
    if not t:
        raise HTTPException(404, "Ticket não encontrado.")
    return _ticket_to_out(t)


@router.patch("/{ticket_id}/status", response_model=TicketOut)
def update_status(ticket_id: int, body: TicketStatusUpdate, db: Session = Depends(_get_db)):
    """Atualiza status do ticket (admin)."""
    t = _svc.update_status(db, ticket_id, body.status, body.resolution)
    if not t:
        raise HTTPException(404, "Ticket não encontrado.")
    return _ticket_to_out(t)


@router.patch("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(
    ticket_id: int,
    user_id: str = Depends(_get_user_id),
    db: Session = Depends(_get_db),
):
    """Atribui ticket a um administrador."""
    t = _svc.assign(db, ticket_id, user_id)
    if not t:
        raise HTTPException(404, "Ticket não encontrado.")
    return _ticket_to_out(t)


@router.post("/{ticket_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    ticket_id: int,
    body: CommentCreate,
    user_id: str = Depends(_get_user_id),
    role: str = Query(default="client"),
    db: Session = Depends(_get_db),
):
    """Adiciona um comentário ao ticket."""
    c = _svc.add_comment(db, ticket_id, user_id, role, body.content)
    if not c:
        raise HTTPException(404, "Ticket não encontrado.")
    return _comment_to_out(c)


@router.get("/{ticket_id}/comments", response_model=list[CommentOut])
def get_comments(ticket_id: int, db: Session = Depends(_get_db)):
    """Lista todos os comentários de um ticket."""
    return [_comment_to_out(c) for c in _svc.get_comments(db, ticket_id)]


# ── Conversores ───────────────────────────────────────────────────────────────

def _ticket_to_out(t) -> dict:
    return {
        "id": t.id,
        "tenant_id": t.tenant_id,
        "created_by": t.created_by,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "category": t.category,
        "assigned_to": t.assigned_to,
        "resolution": t.resolution,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
    }


def _comment_to_out(c) -> dict:
    return {
        "id": c.id,
        "ticket_id": c.ticket_id,
        "author_id": c.author_id,
        "author_role": c.author_role,
        "content": c.content,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
