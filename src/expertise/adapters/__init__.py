"""
Vector store adapters for domain expertise.

Available adapters:
- SupabaseAdapter: Uses Supabase with pgvector
- SQLiteAdapter: Local file-based storage with numpy
"""

from .base import VectorStoreAdapter
from .supabase import SupabaseAdapter
from .sqlite import SQLiteAdapter

__all__ = ["VectorStoreAdapter", "SupabaseAdapter", "SQLiteAdapter"]
