"""Add the Phase 4 agent runtime persistence model.

Revision ID: 20260825_0004
Revises: 20260825_0003
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260825_0004"
down_revision: str | None = "20260825_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    run_status = postgresql.ENUM("pending", "planning", "running", "waiting_approval", "completed", "failed", "cancelled", name="agent_run_status", create_type=False)
    approval_status = postgresql.ENUM("pending", "approved", "rejected", "expired", name="agent_approval_status", create_type=False)
    run_status.create(op.get_bind())
    approval_status.create(op.get_bind())
    op.add_column("agents", sa.Column("enabled_tools", postgresql.JSONB(), server_default="[]", nullable=False))
    op.create_table("agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL")),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("status", run_status, nullable=False, server_default="pending"),
        sa.Column("input", sa.Text(), nullable=False), sa.Column("state", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("final_answer", sa.Text()), sa.Column("error", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)), sa.Column("step_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_duration_ms", sa.Float()), sa.Column("model_provider", sa.String(100)), sa.Column("model_name", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_agent_runs_agent_id", "agent_runs", ["agent_id"]); op.create_index("ix_agent_runs_workspace_id", "agent_runs", ["workspace_id"])
    op.create_table("agent_run_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False), sa.Column("node", sa.String(100), nullable=False), sa.Column("status", sa.String(50), nullable=False),
        sa.Column("input", postgresql.JSONB(), nullable=False), sa.Column("output", postgresql.JSONB(), nullable=False), sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_agent_run_steps_agent_run_id", "agent_run_steps", ["agent_run_id"])
    op.create_table("agent_approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_call_id", sa.String(100), nullable=False), sa.Column("tool_name", sa.String(200), nullable=False), sa.Column("action_description", sa.Text(), nullable=False),
        sa.Column("arguments", postgresql.JSONB(), nullable=False), sa.Column("risk_level", sa.String(20), nullable=False), sa.Column("status", approval_status, server_default="pending", nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("decision_reason", sa.Text()))
    op.create_index("ix_agent_approval_requests_agent_run_id", "agent_approval_requests", ["agent_run_id"])


def downgrade() -> None:
    op.drop_table("agent_approval_requests"); op.drop_table("agent_run_steps"); op.drop_table("agent_runs")
    op.drop_column("agents", "enabled_tools")
    sa.Enum(name="agent_approval_status").drop(op.get_bind()); sa.Enum(name="agent_run_status").drop(op.get_bind())
