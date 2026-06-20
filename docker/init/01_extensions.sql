-- Local Postgres bootstrap (runs once on first container start).
-- Atlas owns the schema; this only enables extensions Atlas migrations rely on.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
