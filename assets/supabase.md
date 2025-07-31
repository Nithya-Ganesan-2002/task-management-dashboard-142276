# Supabase Integration for Task Manager Backend

## Overview
The backend uses Supabase both for authentication (sign up/login) and as a persistent database for storing user tasks.

### Database Tables and Schema

#### **Users Table**
- `id`: uuid, primary key, default `gen_random_uuid()`, matches Supabase Auth user id
- `email`: text, required
- `password_hash`: text, required
- `name`: text, optional
- `created_at`: timestamp, default now()
- **RLS enabled:** Users can only select/update their own row (`auth.uid() = id`)

#### **Tasks Table**
| Column       | Type      | Required | Default           | Description                            |
|--------------|-----------|----------|-------------------|----------------------------------------|
| id           | uuid      | YES      | gen_random_uuid() | Task unique id                         |
| user_id      | uuid      | YES      |                   | Owner (auth.uid from Supabase)         |
| title        | text      | YES      |                   | Task title                             |
| description  | text      | NO       |                   | Optional description                   |
| completed    | boolean   | YES      | false             | Completion status                      |
| created_at   | timestamp | YES      | now()             | Creation timestamp                     |
| updated_at   | timestamp | YES      | now()             | Last update timestamp                  |

- 'updated_at' field automatically updates on any change (trigger installed)
- RLS enabled: Only owner (auth.uid() = user_id) can access/modify a task

## Authentication

- `/signup` and `/login` endpoints use Supabase Auth REST API.
- JWT tokens issued by Supabase are validated for protected routes via `/auth/v1/user`.
- All authenticated endpoints require an `Authorization: Bearer <jwt>` header.

## Backend Environment Variables Required
These **must be set in your backend .env**:
- `SUPABASE_URL`: The Supabase project URL
- `SUPABASE_KEY`: Supabase service role key
- `SUPABASE_ANON_KEY`: (Optional. Defaults to SUPABASE_KEY) - anonymous/public API key
- `SITE_URL`: The frontend base URL for email link redirects during sign up/login

> **NOTE:** As of now, the backend .env does **not** contain these variables. Please add them:

Example:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=YOUR-SUPABASE-SERVICE-ROLE-KEY
SUPABASE_ANON_KEY=YOUR-SUPABASE-ANON-KEY
SITE_URL=http://localhost:3000/
```

See also: [Supabase Auth API Reference](https://supabase.com/docs/reference/auth/sign-up), [Supabase Python Client](https://github.com/supabase-community/supabase-py)

## Additional Notes

- The backend uses the [supabase-py](https://github.com/supabase-community/supabase-py) client library. Ensure it is listed in requirements.
- Users must set environment variables before starting the backend or API functionality will not work.

### RLS SQL (for reference)

```
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users access their own profile" ON users;
CREATE POLICY "Users access their own profile" ON users USING (auth.uid() = id);

ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can access their tasks only" ON tasks;
CREATE POLICY "Users can access their tasks only" ON tasks USING (auth.uid() = user_id);
```
