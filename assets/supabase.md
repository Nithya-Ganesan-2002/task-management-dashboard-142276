# Supabase Integration for Task Manager Backend

## Overview
The backend uses Supabase both for authentication (sign up/login) and as a persistent database for storing user tasks.

## Authentication

- `/signup` and `/login` endpoints utilize Supabase Auth REST API.
- JWT tokens issued by Supabase are validated for protected routes.
- All authenticated endpoints require an `Authorization: Bearer <jwt>` header.

## Task Storage

- Tasks are stored in a Supabase table named `tasks` with columns:
    - `id`: integer, primary key
    - `user_id`: uuid, required (corresponds to Supabase auth user id)
    - `title`: text, required
    - `description`: text, optional
    - `completed`: boolean, default false
    - `created_at`/`updated_at`: timestamps

- Each operation (`insert`, `update`, `delete`, `select`) is scoped to the authenticated user's `user_id`.

## Environment Variables Required

- `SUPABASE_URL`: The Supabase project URL
- `SUPABASE_KEY`: Supabase service role key
- `SUPABASE_ANON_KEY`: (optional, defaults to SUPABASE_KEY) - anonymous/public API key
- `SITE_URL`: The frontend base URL for email link redirect (used in signup)

These variables must be set in the environment for the backend to work correctly.

## Supabase Python Client

- The backend uses the `supabase` Python client library to interact with project tables.

## Setup Notes

1. In your Supabase instance, create the `tasks` table with appropriate columns/row-level security (RLS) so users can only access their own tasks.
2. Set the required environment variables (above) on deployment.

## References

- [Supabase Auth API Reference](https://supabase.com/docs/reference/auth/sign-up)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
