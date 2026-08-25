import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin


class DataSource(UUIDTimestampMixin, Base):
    __tablename__ = "data_sources"
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(30), default="postgresql")
    description: Mapped[str | None] = mapped_column(Text)
    connection_config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    allowed_schemas: Mapped[list[str]] = mapped_column(JSONB, default=lambda: ["public"])
    allowed_tables: Mapped[list[str]] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class DemoRegion(Base):
    __tablename__ = "demo_regions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class DemoProduct(Base):
    __tablename__ = "demo_products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))


class CustomerProfile(UUIDTimestampMixin, Base):
    __tablename__ = "customer_profiles"
    customer_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    region_id: Mapped[int | None] = mapped_column(ForeignKey("demo_regions.id"))
    tier: Mapped[str] = mapped_column(String(30), default="standard")


class CustomerOrder(Base):
    __tablename__ = "customer_orders"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customer_profiles.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("demo_products.id"))
    region_id: Mapped[int] = mapped_column(ForeignKey("demo_regions.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(40))
    refund_status: Mapped[str] = mapped_column(String(40), default="none")
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class SupportTicket(UUIDTimestampMixin, Base):
    __tablename__ = "support_tickets"
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customer_profiles.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="open")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))


class RefundRequest(Base):
    __tablename__ = "refund_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customer_profiles.id", ondelete="CASCADE"), index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customer_orders.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentAnalysis(UUIDTimestampMixin, Base):
    __tablename__ = "document_analyses"
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), unique=True, index=True)
    document_type: Mapped[str] = mapped_column(String(30))
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    extraction: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    model_provider: Mapped[str | None] = mapped_column(String(100))
    model_name: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="completed")


class DocumentRisk(Base):
    __tablename__ = "document_risks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("document_analyses.id", ondelete="CASCADE"), index=True)
    rule_id: Mapped[str | None] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(20))
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer)
    risk_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)


class DocumentComparison(UUIDTimestampMixin, Base):
    __tablename__ = "document_comparisons"
    document_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"))
    document_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"))
    result: Mapped[dict[str, Any]] = mapped_column(JSONB)
