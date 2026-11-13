from functools import lru_cache
from supabase import create_client, Client
from .config import settings

@lru_cache
def get_admin_supabase() -> Client:
    # Service-role key bypasses RLS. Never expose it to the browser.
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

def get_public_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_anon_key)
