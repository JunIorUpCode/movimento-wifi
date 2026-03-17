"""002_indexes_and_constraints — Índices de performance e constraints adicionais

Revision ID: 002
Revises: 001
Create Date: 2026-03-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Índice composto para queries de eventos por tenant + período (muito frequente)
    op.create_index(
        "ix_events_tenant_detected",
        "events",
        ["tenant_id", "detected_at"],
        schema="event_schema",
    )

    # Índice composto para queries de eventos por tenant + tipo
    op.create_index(
        "ix_events_tenant_type",
        "events",
        ["tenant_id", "event_type"],
        schema="event_schema",
    )

    # Índice para busca de dispositivos por tenant
    op.create_index(
        "ix_devices_tenant_status",
        "devices",
        ["tenant_id", "status"],
        schema="device_schema",
    )

    # Índice para heartbeat monitoring (dispositivos offline)
    op.create_index(
        "ix_devices_last_heartbeat",
        "devices",
        ["last_heartbeat"],
        schema="device_schema",
    )

    # Índice para faturas por tenant + status (billing dashboard)
    op.create_index(
        "ix_invoices_tenant_status",
        "invoices",
        ["tenant_id", "status"],
        schema="billing_schema",
    )

    # Índice para busca de tickets por tenant + status
    op.create_index(
        "ix_tickets_tenant_status",
        "support_tickets",
        ["tenant_id", "status"],
        schema="support_schema",
    )

    # Partial index: tickets abertos (os mais consultados)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tickets_open ON support_schema.support_tickets (tenant_id, created_at DESC) WHERE status IN ('open', 'in_progress')"
    )

    # Partial index: eventos de alta confiança (para ML feedback)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_events_high_confidence ON event_schema.events (tenant_id, detected_at DESC) WHERE confidence >= 0.7"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS event_schema.ix_events_high_confidence")
    op.execute("DROP INDEX IF EXISTS support_schema.ix_tickets_open")
    op.drop_index("ix_tickets_tenant_status",  table_name="support_tickets", schema="support_schema")
    op.drop_index("ix_invoices_tenant_status",  table_name="invoices",         schema="billing_schema")
    op.drop_index("ix_devices_last_heartbeat",  table_name="devices",           schema="device_schema")
    op.drop_index("ix_devices_tenant_status",   table_name="devices",           schema="device_schema")
    op.drop_index("ix_events_tenant_type",      table_name="events",            schema="event_schema")
    op.drop_index("ix_events_tenant_detected",  table_name="events",            schema="event_schema")
