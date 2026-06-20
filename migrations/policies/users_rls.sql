-- Canonical RLS policy for the users table (tenant isolation).
-- Reviewed independently of the table DDL; applied via Atlas in
-- versions/20260620000100_rls_policies.sql.
ALTER TABLE "users" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "users" FORCE ROW LEVEL SECURITY;
CREATE POLICY "tenant_isolation" ON "users"
    USING ("tenant_id" = current_setting('app.tenant_id', true)::uuid)
    WITH CHECK ("tenant_id" = current_setting('app.tenant_id', true)::uuid);
