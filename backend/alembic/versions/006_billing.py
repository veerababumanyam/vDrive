"""Create billing and subscription tables

Revision ID: 006_billing
Revises: 005_clients_bookings
Create Date: 2025-01-01 00:05:00.000000

Tables:
- subscription_plans: Available subscription tiers
- subscriptions: Workspace subscriptions
- invoices: Billing invoices
- payment_methods: Stored payment methods
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006_billing"
down_revision: Union[str, None] = "005_clients_bookings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Subscription plans table
    op.create_table(
        "subscription_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        # Pricing
        sa.Column("price_monthly", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_yearly", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        # External IDs
        sa.Column("stripe_price_id_monthly", sa.String(100), nullable=True),
        sa.Column("stripe_price_id_yearly", sa.String(100), nullable=True),
        sa.Column("razorpay_plan_id_monthly", sa.String(100), nullable=True),
        sa.Column("razorpay_plan_id_yearly", sa.String(100), nullable=True),
        # Limits
        sa.Column("storage_limit_gb", sa.Integer(), nullable=False),
        sa.Column("member_limit", sa.Integer(), nullable=False),
        sa.Column("gallery_limit", sa.Integer(), nullable=True),  # Null = unlimited
        sa.Column("client_limit", sa.Integer(), nullable=True),
        # Features
        sa.Column("features", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("feature_flags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        # Status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),  # Shown on pricing page
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        # Trial
        sa.Column("trial_days", sa.Integer(), nullable=False, server_default="14"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for subscription_plans
    op.create_index("ix_subscription_plans_slug", "subscription_plans", ["slug"])
    op.create_index("ix_subscription_plans_is_active", "subscription_plans", ["is_active"])

    # Subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False),
        # Billing info
        sa.Column("billing_email", sa.String(255), nullable=True),
        sa.Column("billing_name", sa.String(200), nullable=True),
        sa.Column("billing_address", postgresql.JSONB(), nullable=True),
        # External IDs
        sa.Column("stripe_customer_id", sa.String(100), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(100), nullable=True),
        sa.Column("razorpay_customer_id", sa.String(100), nullable=True),
        sa.Column("razorpay_subscription_id", sa.String(100), nullable=True),
        # Billing cycle
        sa.Column("billing_interval", sa.String(20), nullable=False, server_default="monthly"),  # monthly, yearly
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="trialing"),
        # trialing, active, past_due, cancelled, paused
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
        # Trial
        sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        # Payment
        sa.Column("default_payment_method_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK added after payment_methods
        sa.Column("last_payment_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_payment_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("next_payment_at", sa.DateTime(timezone=True), nullable=True),
        # Discounts
        sa.Column("discount_code", sa.String(50), nullable=True),
        sa.Column("discount_percent", sa.Integer(), nullable=True),
        sa.Column("discount_expires_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for subscriptions
    op.create_index("ix_subscriptions_workspace_id", "subscriptions", ["workspace_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index("ix_subscriptions_stripe_customer_id", "subscriptions", ["stripe_customer_id"])
    op.create_index("ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"])

    # Invoices table
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True),
        # Invoice details
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        # External IDs
        sa.Column("stripe_invoice_id", sa.String(100), nullable=True),
        sa.Column("razorpay_invoice_id", sa.String(100), nullable=True),
        # Amounts
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("tax", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("discount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("amount_paid", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("amount_due", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        # Line items
        sa.Column("line_items", postgresql.JSONB(), nullable=False, server_default="[]"),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        # draft, open, paid, void, uncollectible
        # Dates
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        # PDF
        sa.Column("pdf_url", sa.String(2048), nullable=True),
        sa.Column("hosted_invoice_url", sa.String(2048), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for invoices
    op.create_index("ix_invoices_workspace_id", "invoices", ["workspace_id"])
    op.create_index("ix_invoices_subscription_id", "invoices", ["subscription_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"])
    op.create_index("ix_invoices_stripe_invoice_id", "invoices", ["stripe_invoice_id"])

    # Payment methods table
    op.create_table(
        "payment_methods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        # External IDs
        sa.Column("stripe_payment_method_id", sa.String(100), nullable=True),
        sa.Column("razorpay_token_id", sa.String(100), nullable=True),
        # Card details (for display only - actual card is stored by Stripe/Razorpay)
        sa.Column("type", sa.String(20), nullable=False),  # card, bank_account, upi
        sa.Column("brand", sa.String(50), nullable=True),  # visa, mastercard, amex
        sa.Column("last_four", sa.String(4), nullable=True),
        sa.Column("exp_month", sa.Integer(), nullable=True),
        sa.Column("exp_year", sa.Integer(), nullable=True),
        sa.Column("cardholder_name", sa.String(200), nullable=True),
        # For bank accounts
        sa.Column("bank_name", sa.String(200), nullable=True),
        sa.Column("account_last_four", sa.String(4), nullable=True),
        # Status
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for payment_methods
    op.create_index("ix_payment_methods_workspace_id", "payment_methods", ["workspace_id"])
    op.create_index("ix_payment_methods_stripe_payment_method_id", "payment_methods", ["stripe_payment_method_id"])

    # Add FK for default_payment_method_id in subscriptions
    op.create_foreign_key(
        "fk_subscriptions_default_payment_method",
        "subscriptions", "payment_methods",
        ["default_payment_method_id"], ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_subscriptions_default_payment_method", "subscriptions", type_="foreignkey")
    op.drop_table("payment_methods")
    op.drop_table("invoices")
    op.drop_table("subscriptions")
    op.drop_table("subscription_plans")
