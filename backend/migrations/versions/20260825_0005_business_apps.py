"""Add Phase 5 business application models.

Revision ID: 20260825_0005
Revises: 20260825_0004
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260825_0005"
down_revision: str | None = "20260825_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps():
    return [sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)]


def upgrade() -> None:
    op.create_table("data_sources", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("type", sa.String(30), nullable=False), sa.Column("description", sa.Text()), sa.Column("connection_config", postgresql.JSONB(), nullable=False), sa.Column("allowed_schemas", postgresql.JSONB(), nullable=False), sa.Column("allowed_tables", postgresql.JSONB(), nullable=False), sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False), *timestamps())
    op.create_index("ix_data_sources_workspace_id", "data_sources", ["workspace_id"])
    op.create_table("demo_regions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(100), unique=True, nullable=False))
    op.create_table("demo_products", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("category", sa.String(100), nullable=False))
    op.create_table("customer_profiles", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("customer_code", sa.String(30), unique=True, nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("email", sa.String(320), nullable=False), sa.Column("region_id", sa.Integer(), sa.ForeignKey("demo_regions.id")), sa.Column("tier", sa.String(30), nullable=False), *timestamps())
    op.create_index("ix_customer_profiles_customer_code", "customer_profiles", ["customer_code"])
    op.create_table("customer_orders", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("order_code", sa.String(40), unique=True, nullable=False), sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customer_profiles.id", ondelete="CASCADE"), nullable=False), sa.Column("product_id", sa.Integer(), sa.ForeignKey("demo_products.id"), nullable=False), sa.Column("region_id", sa.Integer(), sa.ForeignKey("demo_regions.id"), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("amount", sa.Numeric(14,2), nullable=False), sa.Column("status", sa.String(40), nullable=False), sa.Column("refund_status", sa.String(40), nullable=False), sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_customer_orders_customer_id", "customer_orders", ["customer_id"]); op.create_index("ix_customer_orders_ordered_at", "customer_orders", ["ordered_at"])
    op.create_table("support_tickets", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customer_profiles.id", ondelete="CASCADE"), nullable=False), sa.Column("subject", sa.String(500), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("status", sa.String(40), nullable=False), sa.Column("priority", sa.String(20), nullable=False), sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")), *timestamps())
    op.create_table("refund_requests", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customer_profiles.id", ondelete="CASCADE"), nullable=False), sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customer_orders.id", ondelete="CASCADE"), nullable=False), sa.Column("amount", sa.Numeric(14,2), nullable=False), sa.Column("reason", sa.Text(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("decided_at", sa.DateTime(timezone=True)))
    op.create_table("document_analyses", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), unique=True, nullable=False), sa.Column("document_type", sa.String(30), nullable=False), sa.Column("summary", postgresql.JSONB(), nullable=False), sa.Column("extraction", postgresql.JSONB(), nullable=False), sa.Column("citations", postgresql.JSONB(), nullable=False), sa.Column("model_provider", sa.String(100)), sa.Column("model_name", sa.String(100)), sa.Column("status", sa.String(30), nullable=False), *timestamps())
    op.create_table("document_risks", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_analyses.id", ondelete="CASCADE"), nullable=False), sa.Column("rule_id", sa.String(100)), sa.Column("source", sa.String(20), nullable=False), sa.Column("severity", sa.String(20), nullable=False), sa.Column("title", sa.String(300), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("evidence", sa.Text(), nullable=False), sa.Column("page", sa.Integer()), sa.Column("metadata", postgresql.JSONB(), nullable=False))
    op.create_table("document_comparisons", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("document_a_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False), sa.Column("document_b_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False), sa.Column("result", postgresql.JSONB(), nullable=False), *timestamps())


def downgrade() -> None:
    for table in ("document_comparisons","document_risks","document_analyses","refund_requests","support_tickets","customer_orders","customer_profiles","demo_products","demo_regions","data_sources"): op.drop_table(table)
