"""001_initial_schema — Schema inicial completo do WiFiSense SaaS

Revision ID: 001
Revises:
Create Date: 2026-03-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Schema auth ───────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS auth_schema")

    op.create_table(
        "users",
        sa.Column("id",            sa.String(36),  primary_key=True),
        sa.Column("tenant_id",     sa.String(36),  nullable=False, index=True),
        sa.Column("email",         sa.String(255), nullable=False),
        sa.Column("name",          sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(500), nullable=False),
        sa.Column("role",          sa.String(20),  nullable=False, server_default="client"),
        sa.Column("is_active",     sa.Boolean(),   nullable=False, server_default="true"),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until",  sa.DateTime(),  nullable=True),
        sa.Column("deleted_at",    sa.DateTime(),  nullable=True),
        sa.Column("created_at",    sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",    sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        schema="auth_schema",
    )
    op.create_unique_constraint("uq_users_email", "users", ["email"], schema="auth_schema")
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"], schema="auth_schema")

    op.create_table(
        "audit_logs",
        sa.Column("id",          sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id",     sa.String(36),   nullable=True),
        sa.Column("tenant_id",   sa.String(36),   nullable=True),
        sa.Column("action",      sa.String(100),  nullable=False),
        sa.Column("resource",    sa.String(200),  nullable=True),
        sa.Column("ip_address",  sa.String(45),   nullable=True),
        sa.Column("success",     sa.Boolean(),    nullable=False),
        sa.Column("created_at",  sa.DateTime(),   nullable=False, server_default=sa.func.now()),
        schema="auth_schema",
    )
    op.create_index("ix_audit_user_id", "audit_logs", ["user_id"], schema="auth_schema")
    op.create_index("ix_audit_created_at", "audit_logs", ["created_at"], schema="auth_schema")

    # ── Schema tenant ─────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS tenant_schema")

    op.create_table(
        "tenants",
        sa.Column("id",           sa.String(36),  primary_key=True),
        sa.Column("name",         sa.String(200), nullable=False),
        sa.Column("email",        sa.String(255), nullable=False),
        sa.Column("plan",         sa.String(20),  nullable=False, server_default="trial"),
        sa.Column("status",       sa.String(20),  nullable=False, server_default="active"),
        sa.Column("trial_ends_at",sa.DateTime(),  nullable=True),
        sa.Column("created_at",   sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",   sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        schema="tenant_schema",
    )
    op.create_unique_constraint("uq_tenants_email", "tenants", ["email"], schema="tenant_schema")

    # ── Schema device ─────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS device_schema")

    op.create_table(
        "devices",
        sa.Column("id",              sa.String(36),  primary_key=True),
        sa.Column("tenant_id",       sa.String(36),  nullable=False, index=True),
        sa.Column("name",            sa.String(200), nullable=True),
        sa.Column("activation_key",  sa.String(100), nullable=False),
        sa.Column("hardware_type",   sa.String(50),  nullable=True),
        sa.Column("status",          sa.String(20),  nullable=False, server_default="active"),
        sa.Column("last_heartbeat",  sa.DateTime(),  nullable=True),
        sa.Column("created_at",      sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        schema="device_schema",
    )

    # ── Schema event ──────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS event_schema")

    op.create_table(
        "events",
        sa.Column("id",          sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id",   sa.String(36),   nullable=False),
        sa.Column("device_id",   sa.String(36),   nullable=False),
        sa.Column("event_type",  sa.String(50),   nullable=False),
        sa.Column("confidence",  sa.Float(),      nullable=False),
        sa.Column("rssi",        sa.Float(),      nullable=True),
        sa.Column("features",    sa.JSON(),       nullable=True),
        sa.Column("detected_at", sa.DateTime(),   nullable=False, server_default=sa.func.now()),
        schema="event_schema",
    )
    op.create_index("ix_events_tenant_id",   "events", ["tenant_id"],   schema="event_schema")
    op.create_index("ix_events_detected_at", "events", ["detected_at"], schema="event_schema")
    op.create_index("ix_events_event_type",  "events", ["event_type"],  schema="event_schema")

    # ── Schema license ────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS license_schema")

    op.create_table(
        "licenses",
        sa.Column("id",             sa.String(36),  primary_key=True),
        sa.Column("tenant_id",      sa.String(36),  nullable=False, index=True),
        sa.Column("key",            sa.String(50),  nullable=False),
        sa.Column("plan",           sa.String(20),  nullable=False),
        sa.Column("max_devices",    sa.Integer(),   nullable=False, server_default="1"),
        sa.Column("status",         sa.String(20),  nullable=False, server_default="active"),
        sa.Column("expires_at",     sa.DateTime(),  nullable=True),
        sa.Column("created_at",     sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        schema="license_schema",
    )
    op.create_unique_constraint("uq_licenses_key", "licenses", ["key"], schema="license_schema")

    # ── Schema notification ───────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS notification_schema")

    op.create_table(
        "notification_logs",
        sa.Column("id",         sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id",  sa.String(36),   nullable=False, index=True),
        sa.Column("event_id",   sa.BigInteger(), nullable=True),
        sa.Column("channel",    sa.String(50),   nullable=False),
        sa.Column("status",     sa.String(20),   nullable=False),
        sa.Column("error_msg",  sa.Text(),       nullable=True),
        sa.Column("sent_at",    sa.DateTime(),   nullable=False, server_default=sa.func.now()),
        schema="notification_schema",
    )

    # ── Schema billing ────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS billing_schema")

    op.create_table(
        "invoices",
        sa.Column("id",             sa.String(36),  primary_key=True),
        sa.Column("tenant_id",      sa.String(36),  nullable=False, index=True),
        sa.Column("amount_cents",   sa.Integer(),   nullable=False),
        sa.Column("currency",       sa.String(3),   nullable=False, server_default="BRL"),
        sa.Column("status",         sa.String(20),  nullable=False, server_default="pending"),
        sa.Column("stripe_id",      sa.String(200), nullable=True),
        sa.Column("due_date",       sa.Date(),      nullable=True),
        sa.Column("paid_at",        sa.DateTime(),  nullable=True),
        sa.Column("created_at",     sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        schema="billing_schema",
    )

    # ── Schema support (tickets) ──────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS support_schema")

    op.create_table(
        "support_tickets",
        sa.Column("id",           sa.Integer(),  primary_key=True, autoincrement=True),
        sa.Column("tenant_id",    sa.String(36), nullable=False, index=True),
        sa.Column("created_by",   sa.String(36), nullable=False),
        sa.Column("title",        sa.String(200),nullable=False),
        sa.Column("description",  sa.Text(),     nullable=False),
        sa.Column("status",       sa.String(20), nullable=False, server_default="open"),
        sa.Column("priority",     sa.String(20), nullable=False, server_default="medium"),
        sa.Column("category",     sa.String(50), nullable=False, server_default="general"),
        sa.Column("assigned_to",  sa.String(36), nullable=True),
        sa.Column("resolution",   sa.Text(),     nullable=True),
        sa.Column("created_at",   sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",   sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at",  sa.DateTime(), nullable=True),
        schema="support_schema",
    )

    op.create_table(
        "ticket_comments",
        sa.Column("id",          sa.Integer(),  primary_key=True, autoincrement=True),
        sa.Column("ticket_id",   sa.Integer(),  nullable=False, index=True),
        sa.Column("author_id",   sa.String(36), nullable=False),
        sa.Column("author_role", sa.String(20), nullable=False, server_default="client"),
        sa.Column("content",     sa.Text(),     nullable=False),
        sa.Column("created_at",  sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema="support_schema",
    )


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS support_schema CASCADE")
    op.execute("DROP SCHEMA IF EXISTS billing_schema CASCADE")
    op.execute("DROP SCHEMA IF EXISTS notification_schema CASCADE")
    op.execute("DROP SCHEMA IF EXISTS license_schema CASCADE")
    op.execute("DROP SCHEMA IF EXISTS event_schema CASCADE")
    op.execute("DROP SCHEMA IF EXISTS device_schema CASCADE")
    op.execute("DROP SCHEMA IF EXISTS tenant_schema CASCADE")
    op.execute("DROP SCHEMA IF EXISTS auth_schema CASCADE")
