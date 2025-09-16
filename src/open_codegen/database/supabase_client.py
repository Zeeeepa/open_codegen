"""
Supabase client integration for Open Codegen.

Provides connection management, error handling, and basic operations following KISS principles.
"""

import os
from functools import lru_cache
from typing import Any

import structlog
from pydantic import BaseModel
from supabase import Client, create_client

from open_codegen.utils.error_handler import (
    DatabaseError,
    SupabaseConnectionError,
    safe_parse_error,
)

logger = structlog.get_logger(__name__)


class SupabaseConfig(BaseModel):
    """Supabase configuration model."""

    url: str
    key: str
    timeout: int = 30
    auto_refresh_token: bool = True


class SupabaseClient:
    """
    Supabase client wrapper with error handling and connection management.

    Follows KISS principles with simple connection management and error handling.
    """

    def __init__(self, config: SupabaseConfig) -> None:
        """Initialize Supabase client with configuration."""
        self.config = config
        self._client: Client | None = None
        self._connected = False

    @property
    def client(self) -> Client:
        """Get or create Supabase client instance."""
        if self._client is None:
            try:
                self._client = create_client(
                    supabase_url=self.config.url,
                    supabase_key=self.config.key,
                )
                self._connected = True
                logger.info("Supabase client connected successfully")
            except Exception as e:
                error = safe_parse_error(e, "Failed to connect to Supabase")
                logger.error("Supabase connection failed", error=str(error))
                raise SupabaseConnectionError(str(error)) from e

        return self._client

    async def test_connection(self) -> bool:
        """Test the Supabase connection."""
        try:
            # Simple query to test connection
            self.client.table("user_sessions").select("session_id").limit(1).execute()
            self._connected = True
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            error = safe_parse_error(e, "Connection test failed")
            logger.error("Supabase connection test failed", error=str(error))
            self._connected = False
            return False

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self._client is not None

    async def insert(self, table: str, data: dict[str, Any]) -> dict[str, Any]:
        """Insert data into a table."""
        try:
            result = self.client.table(table).insert(data).execute()
            if result.data:
                logger.debug("Data inserted successfully", table=table)
                return result.data[0]
            else:
                raise DatabaseError("Insert operation returned no data")
        except Exception as e:
            error = safe_parse_error(e, f"Failed to insert into {table}")
            logger.error("Insert operation failed", table=table, error=str(error))
            raise DatabaseError(str(error)) from e

    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Select data from a table with optional filters."""
        try:
            query = self.client.table(table).select(columns)

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            if limit:
                query = query.limit(limit)

            result = query.execute()
            logger.debug("Data selected successfully", table=table, count=len(result.data))
            return result.data
        except Exception as e:
            error = safe_parse_error(e, f"Failed to select from {table}")
            logger.error("Select operation failed", table=table, error=str(error))
            raise DatabaseError(str(error)) from e

    async def update(
        self,
        table: str,
        data: dict[str, Any],
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Update data in a table."""
        try:
            query = self.client.table(table).update(data)

            for key, value in filters.items():
                query = query.eq(key, value)

            result = query.execute()
            logger.debug("Data updated successfully", table=table, count=len(result.data))
            return result.data
        except Exception as e:
            error = safe_parse_error(e, f"Failed to update {table}")
            logger.error("Update operation failed", table=table, error=str(error))
            raise DatabaseError(str(error)) from e

    async def delete(self, table: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Delete data from a table."""
        try:
            query = self.client.table(table).delete()

            for key, value in filters.items():
                query = query.eq(key, value)

            result = query.execute()
            logger.debug("Data deleted successfully", table=table, count=len(result.data))
            return result.data
        except Exception as e:
            error = safe_parse_error(e, f"Failed to delete from {table}")
            logger.error("Delete operation failed", table=table, error=str(error))
            raise DatabaseError(str(error)) from e


@lru_cache
def get_supabase_config() -> SupabaseConfig:
    """Get Supabase configuration from environment variables."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise SupabaseConnectionError(
            "SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required"
        )

    return SupabaseConfig(url=url, key=key)


@lru_cache
def get_supabase_client() -> SupabaseClient:
    """Get cached Supabase client instance."""
    config = get_supabase_config()
    return SupabaseClient(config)
