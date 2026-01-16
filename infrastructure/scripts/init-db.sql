-- ===========================================
-- RawDrive PostgreSQL Initialization Script
-- ===========================================
-- This script runs on first database creation
-- Image: timescale/timescaledb-ha:pg16

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Try to enable pgvectorscale (may not be available in all images)
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS "vectorscale" CASCADE;
    RAISE NOTICE 'pgvectorscale extension enabled successfully';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pgvectorscale extension not available, using pgvector only';
END
$$;

-- Enable TimescaleDB for time-series data (optional)
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS "timescaledb";
    RAISE NOTICE 'TimescaleDB extension enabled successfully';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'TimescaleDB extension not available';
END
$$;

-- ===========================================
-- Create schemas for multi-tenant isolation
-- ===========================================
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS audit;

-- ===========================================
-- Grant permissions
-- ===========================================
GRANT ALL ON SCHEMA app TO RawDrive;
GRANT ALL ON SCHEMA audit TO RawDrive;
GRANT USAGE ON SCHEMA public TO RawDrive;

-- ===========================================
-- Create audit log function
-- ===========================================
CREATE OR REPLACE FUNCTION audit.log_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit.change_log (
            table_name,
            operation,
            old_data,
            changed_at,
            changed_by
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            row_to_json(OLD),
            NOW(),
            current_user
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.change_log (
            table_name,
            operation,
            old_data,
            new_data,
            changed_at,
            changed_by
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            row_to_json(OLD),
            row_to_json(NEW),
            NOW(),
            current_user
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit.change_log (
            table_name,
            operation,
            new_data,
            changed_at,
            changed_by
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            row_to_json(NEW),
            NOW(),
            current_user
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- Create audit log table
-- ===========================================
CREATE TABLE IF NOT EXISTS audit.change_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    changed_by VARCHAR(100)
);

-- Create index for audit log queries
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit.change_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit.change_log(changed_at);

-- ===========================================
-- Create function for updated_at timestamp
-- ===========================================
CREATE OR REPLACE FUNCTION app.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- Create function for gallery stats trigger
-- ===========================================
CREATE OR REPLACE FUNCTION app.update_gallery_stats()
RETURNS TRIGGER AS $$
DECLARE
    v_gallery_id UUID;
BEGIN
    -- Determine which gallery to update
    IF TG_OP = 'DELETE' THEN
        v_gallery_id := OLD.gallery_id;
    ELSE
        v_gallery_id := NEW.gallery_id;
    END IF;

    -- Update denormalized stats (if galleries table exists)
    -- This will be called by Alembic migrations later
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- Verify extensions are enabled
-- ===========================================
DO $$
DECLARE
    ext_name TEXT;
    ext_count INT := 0;
BEGIN
    FOR ext_name IN SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgcrypto', 'pg_trgm', 'vector')
    LOOP
        ext_count := ext_count + 1;
        RAISE NOTICE 'Extension enabled: %', ext_name;
    END LOOP;

    RAISE NOTICE 'Total extensions enabled: %', ext_count;

    IF ext_count < 4 THEN
        RAISE WARNING 'Not all required extensions are enabled!';
    END IF;
END
$$;

-- ===========================================
-- Display vector extension info
-- ===========================================
DO $$
BEGIN
    -- Check vector extension version
    RAISE NOTICE 'pgvector version: %', (SELECT extversion FROM pg_extension WHERE extname = 'vector');

    -- Check if vectorscale is available
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vectorscale') THEN
        RAISE NOTICE 'pgvectorscale is available for large-scale vector operations';
    ELSE
        RAISE NOTICE 'Using pgvector HNSW/IVFFlat indexes (pgvectorscale not available)';
    END IF;
END
$$;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'RawDrive database initialization complete!';
    RAISE NOTICE '===========================================';
END
$$;
