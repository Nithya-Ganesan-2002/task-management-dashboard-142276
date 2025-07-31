"""
Supabase client utility module for backend.

Establishes connection to Supabase to be used for authentication, user management,
and task storage.
"""

import os
from supabase import create_client, Client

# Singleton supabase client instance.
_supabase_client: Client = None

# PUBLIC_INTERFACE
def get_supabase_client() -> Client:
    """
    Returns a singleton Supabase client, connecting with SUPABASE_URL & SUPABASE_KEY from environment.
    """
    global _supabase_client
    if _supabase_client is None:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set in the environment variables")
        _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client
