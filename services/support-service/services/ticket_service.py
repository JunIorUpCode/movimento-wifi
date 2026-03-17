# -*- coding: utf-8 -*-
"""Lógica de negócio do serviço de tickets de suporte."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..models.ticket import Ticket, TicketComment, TicketStatus, TicketPriority


class TicketService:
    """CRUD e regras de negócio para tickets de suporte."""

    def create(
        self,
        db: Session,
        tenant_id: str,
        created_by: str,
        title: str,
        description: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        category: str = "general",
    ) -> Ticket:
        ticket = Ticket(
            tenant_id=tenant_id,
            created_by=created_by,
            title=title,
            description=description,
            priority=priority,
            category=category,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    def list_by_tenant(
        self,
        db: Session,
        tenant_id: str,
        status: Optional[TicketStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Ticket]:
        q = db.query(Ticket).filter(Ticket.tenant_id == tenant_id)
        if status:
            q = q.filter(Ticket.status == status)
        return q.order_by(Ticket.created_at.desc()).limit(limit).offset(offset).all()

    def list_all(
        self,
        db: Session,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Ticket]:
        """Listagem para admins — todos os tenants."""
        q = db.query(Ticket)
        if status:
            q = q.filter(Ticket.status == status)
        if priority:
            q = q.filter(Ticket.priority == priority)
        return q.order_by(Ticket.created_at.desc()).limit(limit).offset(offset).all()

    def get(self, db: Session, ticket_id: int) -> Optional[Ticket]:
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()

    def update_status(
        self, db: Session, ticket_id: int, status: TicketStatus, resolution: Optional[str] = None
    ) -> Optional[Ticket]:
        ticket = self.get(db, ticket_id)
        if not ticket:
            return None
        ticket.status = status
        ticket.updated_at = datetime.utcnow()
        if status == TicketStatus.RESOLVED and resolution:
            ticket.resolution = resolution
            ticket.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(ticket)
        return ticket

    def assign(self, db: Session, ticket_id: int, admin_id: str) -> Optional[Ticket]:
        ticket = self.get(db, ticket_id)
        if not ticket:
            return None
        ticket.assigned_to = admin_id
        ticket.status = TicketStatus.IN_PROGRESS
        ticket.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ticket)
        return ticket

    def add_comment(
        self, db: Session, ticket_id: int, author_id: str, author_role: str, content: str
    ) -> Optional[TicketComment]:
        ticket = self.get(db, ticket_id)
        if not ticket:
            return None
        comment = TicketComment(
            ticket_id=ticket_id,
            author_id=author_id,
            author_role=author_role,
            content=content,
        )
        db.add(comment)
        # Reabre ticket se cliente comentar em ticket fechado
        if author_role == "client" and ticket.status == TicketStatus.CLOSED:
            ticket.status = TicketStatus.OPEN
            ticket.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(comment)
        return comment

    def get_comments(self, db: Session, ticket_id: int) -> list[TicketComment]:
        return (
            db.query(TicketComment)
            .filter(TicketComment.ticket_id == ticket_id)
            .order_by(TicketComment.created_at.asc())
            .all()
        )
