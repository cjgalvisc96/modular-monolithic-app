-- Baseline schema: users, tasks, ai_suggestions.
-- Every table carries the shared base columns (tenant_id, audit, soft-delete,
-- timestamps). RLS is enabled here; the policies themselves are the canonical
-- definitions in migrations/policies/*.sql and are re-applied by the next
-- migration so reviewers see them in one place.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- users -----------------------------------------------------------------------
CREATE TABLE "users" (
    "id"          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "tenant_id"   uuid NOT NULL,
    "email"       varchar(320) NOT NULL,
    "full_name"   varchar(200) NOT NULL,
    "role"        varchar(32)  NOT NULL DEFAULT 'member',
    "is_active"   boolean      NOT NULL DEFAULT true,
    "created_at"  timestamptz  NOT NULL DEFAULT now(),
    "updated_at"  timestamptz  NOT NULL DEFAULT now(),
    "deleted_at"  timestamptz,
    "created_by"  uuid,
    "updated_by"  uuid,
    CONSTRAINT "uq_users_tenant_email" UNIQUE ("tenant_id", "email")
);
CREATE INDEX "ix_users_tenant_id" ON "users" ("tenant_id");
CREATE INDEX "ix_users_deleted_at" ON "users" ("deleted_at");

-- tasks -----------------------------------------------------------------------
CREATE TABLE "tasks" (
    "id"          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "tenant_id"   uuid NOT NULL,
    "owner_id"    uuid NOT NULL,
    "title"       varchar(300) NOT NULL,
    "description" text         NOT NULL DEFAULT '',
    "status"      varchar(20)  NOT NULL DEFAULT 'pending',
    "due_date"    date,
    "created_at"  timestamptz  NOT NULL DEFAULT now(),
    "updated_at"  timestamptz  NOT NULL DEFAULT now(),
    "deleted_at"  timestamptz,
    "created_by"  uuid,
    "updated_by"  uuid
);
CREATE INDEX "ix_tasks_tenant_id" ON "tasks" ("tenant_id");
CREATE INDEX "ix_tasks_owner_id" ON "tasks" ("owner_id");
CREATE INDEX "ix_tasks_deleted_at" ON "tasks" ("deleted_at");

-- ai_suggestions --------------------------------------------------------------
CREATE TABLE "ai_suggestions" (
    "id"          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "tenant_id"   uuid NOT NULL,
    "prompt"      text         NOT NULL,
    "model"       varchar(128) NOT NULL,
    "status"      varchar(20)  NOT NULL DEFAULT 'pending',
    "response"    text,
    "error"       text,
    "created_at"  timestamptz  NOT NULL DEFAULT now(),
    "updated_at"  timestamptz  NOT NULL DEFAULT now(),
    "deleted_at"  timestamptz,
    "created_by"  uuid,
    "updated_by"  uuid
);
CREATE INDEX "ix_ai_suggestions_tenant_id" ON "ai_suggestions" ("tenant_id");
CREATE INDEX "ix_ai_suggestions_deleted_at" ON "ai_suggestions" ("deleted_at");
