"""Initial calendar service schema — all 11 tables.

Revision ID: 0001_initial
Revises: (none — new database)
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── workspaces ──────────────────────────────────────────────────────────
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("workspace_type", sa.String(30), nullable=False, server_default="team"),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_workspaces_company_id", "workspaces", ["company_id"])
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])
    op.create_index("ix_workspaces_company_owner", "workspaces", ["company_id", "owner_id"])
    op.create_index("ix_workspaces_company_active", "workspaces", ["company_id", "is_active"])
    op.create_index("ix_workspaces_company_deleted", "workspaces", ["company_id", "is_deleted"])

    # ── workspace_members ───────────────────────────────────────────────────
    op.create_table(
        "workspace_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime, nullable=False),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("workspace_id", "employee_id", name="uq_workspace_member"),
    )
    op.create_index("ix_workspace_members_company_id", "workspace_members", ["company_id"])
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])
    op.create_index("ix_workspace_members_employee_id", "workspace_members", ["employee_id"])

    # ── calendars ───────────────────────────────────────────────────────────
    op.create_table(
        "calendars",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("calendar_type", sa.String(30), nullable=False, server_default="team"),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("google_calendar_id", sa.String(300), nullable=True),
        sa.Column("public_share_token", sa.String(64), nullable=True, unique=True),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_calendars_company_id", "calendars", ["company_id"])
    op.create_index("ix_calendars_workspace_id", "calendars", ["workspace_id"])
    op.create_index("ix_calendars_owner_id", "calendars", ["owner_id"])
    op.create_index("ix_calendars_google_calendar_id", "calendars", ["google_calendar_id"])
    op.create_index("ix_calendars_public_share_token", "calendars", ["public_share_token"])
    op.create_index("ix_calendars_company_type", "calendars", ["company_id", "calendar_type"])

    # ── calendar_events ─────────────────────────────────────────────────────
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("calendar_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calendars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("event_type", sa.String(30), nullable=False, server_default="meeting"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_day", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("rrule", sa.String(500), nullable=True),
        sa.Column("recurrence_master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attendees", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("google_event_id", sa.String(300), nullable=True),
        sa.Column("google_etag", sa.String(100), nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("reminder_minutes", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("search_vector", sa.Column("search_vector", postgresql.TSVECTOR), nullable=True) if False else sa.Column("search_vector", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    # Use raw SQL for tsvector column and trigger — alembic can't emit these natively
    op.execute("ALTER TABLE calendar_events ALTER COLUMN search_vector TYPE tsvector USING search_vector::tsvector")
    op.create_index("ix_calendar_events_company_id", "calendar_events", ["company_id"])
    op.create_index("ix_calendar_events_calendar_start", "calendar_events", ["calendar_id", "start_time"])
    op.create_index("ix_calendar_events_company_start", "calendar_events", ["company_id", "start_time"])
    op.create_index("ix_calendar_events_created_by", "calendar_events", ["created_by"])
    op.create_index("ix_calendar_events_google_event_id", "calendar_events", ["google_event_id"])
    op.create_index("ix_calendar_events_recurrence_master_id", "calendar_events", ["recurrence_master_id"])
    op.execute("CREATE INDEX ix_calendar_events_search ON calendar_events USING GIN(search_vector)")
    op.execute("""
        CREATE TRIGGER trg_calendar_events_fts
        BEFORE INSERT OR UPDATE ON calendar_events
        FOR EACH ROW EXECUTE FUNCTION
        tsvector_update_trigger(search_vector, 'pg_catalog.english', title, description, location)
    """)

    # ── recurrence_overrides ────────────────────────────────────────────────
    op.create_table(
        "recurrence_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("master_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("override_date", sa.Date, nullable=False),
        sa.Column("action", sa.String(20), nullable=False, server_default="edit"),
        sa.Column("new_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("new_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("new_title", sa.String(500), nullable=True),
        sa.Column("new_description", sa.Text, nullable=True),
        sa.Column("new_location", sa.String(500), nullable=True),
        sa.Column("new_all_day", sa.Boolean, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("master_event_id", "override_date", name="uq_recurrence_override"),
    )
    op.create_index("ix_recurrence_overrides_company_id", "recurrence_overrides", ["company_id"])
    op.create_index("ix_recurrence_overrides_master_event_id", "recurrence_overrides", ["master_event_id"])
    op.create_index("ix_recurrence_overrides_override_date", "recurrence_overrides", ["override_date"])

    # ── calendar_tasks ──────────────────────────────────────────────────────
    op.create_table(
        "calendar_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calendar_events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("parent_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calendar_tasks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="todo"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_hours", sa.Float, nullable=True),
        sa.Column("actual_hours", sa.Float, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("google_tasklist_id", sa.String(300), nullable=True),
        sa.Column("google_task_id", sa.String(300), nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("attachments", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("search_vector", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.execute("ALTER TABLE calendar_tasks ALTER COLUMN search_vector TYPE tsvector USING search_vector::tsvector")
    op.create_index("ix_calendar_tasks_company_id", "calendar_tasks", ["company_id"])
    op.create_index("ix_calendar_tasks_workspace_status", "calendar_tasks", ["workspace_id", "status"])
    op.create_index("ix_calendar_tasks_company_status", "calendar_tasks", ["company_id", "status"])
    op.create_index("ix_calendar_tasks_due_date", "calendar_tasks", ["due_date"])
    op.create_index("ix_calendar_tasks_created_by", "calendar_tasks", ["created_by"])
    op.create_index("ix_calendar_tasks_parent_task_id", "calendar_tasks", ["parent_task_id"])
    op.create_index("ix_calendar_tasks_google_task_id", "calendar_tasks", ["google_task_id"])
    op.execute("CREATE INDEX ix_calendar_tasks_search ON calendar_tasks USING GIN(search_vector)")
    op.execute("""
        CREATE TRIGGER trg_calendar_tasks_fts
        BEFORE INSERT OR UPDATE ON calendar_tasks
        FOR EACH ROW EXECUTE FUNCTION
        tsvector_update_trigger(search_vector, 'pg_catalog.english', title, description)
    """)

    # ── task_assignees ──────────────────────────────────────────────────────
    op.create_table(
        "task_assignees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calendar_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime, nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_task_assignees_company_id", "task_assignees", ["company_id"])
    op.create_index("ix_task_assignees_task_id", "task_assignees", ["task_id"])
    op.create_index("ix_task_assignees_employee_id", "task_assignees", ["employee_id"])

    # ── task_comments ───────────────────────────────────────────────────────
    op.create_table(
        "task_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calendar_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_comment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("task_comments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("search_vector", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("edited_at", sa.DateTime, nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.execute("ALTER TABLE task_comments ALTER COLUMN search_vector TYPE tsvector USING search_vector::tsvector")
    op.create_index("ix_task_comments_company_id", "task_comments", ["company_id"])
    op.create_index("ix_task_comments_task_id", "task_comments", ["task_id"])
    op.create_index("ix_task_comments_author_id", "task_comments", ["author_id"])
    op.create_index("ix_task_comments_parent_comment_id", "task_comments", ["parent_comment_id"])
    op.execute("CREATE INDEX ix_task_comments_search ON task_comments USING GIN(search_vector)")
    op.execute("""
        CREATE TRIGGER trg_task_comments_fts
        BEFORE INSERT OR UPDATE ON task_comments
        FOR EACH ROW EXECUTE FUNCTION
        tsvector_update_trigger(search_vector, 'pg_catalog.english', body)
    """)

    # ── google_integrations ─────────────────────────────────────────────────
    op.create_table(
        "google_integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("google_email", sa.String(300), nullable=True),
        sa.Column("access_token", sa.Text, nullable=True),
        sa.Column("refresh_token", sa.Text, nullable=True),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text, nullable=True),
        sa.Column("connected_calendars", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_error_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("next_sync_allowed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_google_integrations_company_id", "google_integrations", ["company_id"])
    op.create_index("ix_google_integrations_employee_id", "google_integrations", ["employee_id"])
    op.create_index("ix_google_integrations_status", "google_integrations", ["status"])

    # ── sync_logs ───────────────────────────────────────────────────────────
    op.create_table(
        "sync_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("google_integrations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("resource_type", sa.String(30), nullable=False),
        sa.Column("local_resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("google_resource_id", sa.String(300), nullable=True),
        sa.Column("sync_direction", sa.String(20), nullable=False),
        sa.Column("sync_status", sa.String(30), nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_sync_token", sa.String(500), nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_sync_logs_company_id", "sync_logs", ["company_id"])
    op.create_index("ix_sync_logs_employee_id", "sync_logs", ["employee_id"])
    op.create_index("ix_sync_logs_integration_id", "sync_logs", ["integration_id"])
    op.create_index("ix_sync_logs_resource_type", "sync_logs", ["resource_type"])
    op.create_index("ix_sync_logs_sync_status", "sync_logs", ["sync_status"])
    op.create_index("ix_sync_logs_synced_at", "sync_logs", ["synced_at"])

    # ── calendar_audit_logs ─────────────────────────────────────────────────
    op.create_table(
        "calendar_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_role", sa.String(30), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("before_state", postgresql.JSONB, nullable=True),
        sa.Column("after_state", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_company_id", "calendar_audit_logs", ["company_id"])
    op.create_index("ix_audit_logs_actor_id", "calendar_audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_resource_type", "calendar_audit_logs", ["resource_type"])
    op.create_index("ix_audit_logs_resource_id", "calendar_audit_logs", ["resource_id"])
    op.create_index("ix_audit_logs_action", "calendar_audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "calendar_audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_company_resource", "calendar_audit_logs", ["company_id", "resource_type", "resource_id"])
    op.create_index("ix_audit_logs_company_actor", "calendar_audit_logs", ["company_id", "actor_id"])


def downgrade() -> None:
    op.drop_table("calendar_audit_logs")
    op.drop_table("sync_logs")
    op.drop_table("google_integrations")
    op.drop_table("task_comments")
    op.drop_table("task_assignees")
    op.drop_table("calendar_tasks")
    op.drop_table("recurrence_overrides")
    op.drop_table("calendar_events")
    op.drop_table("calendars")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
