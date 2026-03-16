-- ============================================================
--  Create Ophillia company + Super Admin user
--  Email    : abhinav@ophillia.com
--  Password : Admin@123
--  Role     : super_admin
--
--  Run against the auth_db database:
--    docker exec -i hrms-db psql -U postgres -d auth_db < scripts/create_superadmin.sql
-- ============================================================

BEGIN;

-- 1. Create company (idempotent)
INSERT INTO companies (id, name, domain, is_active, created_at)
VALUES (
    gen_random_uuid(),
    'Ophillia',
    'ophillia.com',
    TRUE,
    NOW()
)
ON CONFLICT (name) DO NOTHING;

-- 2. Create super admin user (idempotent)
INSERT INTO users (id, company_id, email, hashed_password, role, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    (SELECT id FROM companies WHERE name = 'Ophillia'),
    'abhinav@ophillia.com',
    '$argon2id$v=19$m=65536,t=3,p=4$YYzxvpdyjhFiDCGEMCbkvA$b90h7ZoFzFvHPoRbgnweKT1n0/PX0grFEAVoEZWrF0o',
    'super_admin',
    TRUE,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
    SET role        = 'super_admin',
        is_active   = TRUE,
        updated_at  = NOW();

COMMIT;

-- Confirm
SELECT
    u.id,
    u.email,
    u.role,
    u.is_active,
    c.name AS company
FROM users u
JOIN companies c ON c.id = u.company_id
WHERE u.email = 'abhinav@ophillia.com';
