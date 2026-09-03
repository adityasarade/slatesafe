"""A minimal client for the official mcp-clickhouse stdio server.

The contest requires the official MCP server to be used at runtime. This module
launches that server and calls its `run_query` tool; credentials remain in the
environment and never reach the browser.
"""

from __future__ import annotations

import os
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ClickHouseMcpGateway:
    def _env(self) -> dict[str, str]:
        required = ("CLICKHOUSE_HOST", "CLICKHOUSE_USER", "CLICKHOUSE_PASSWORD")
        missing = [name for name in required if os.getenv(name) is None]
        if missing:
            raise RuntimeError(f"ClickHouse credentials missing: {', '.join(missing)}")
        return {
            "CLICKHOUSE_HOST": os.environ["CLICKHOUSE_HOST"],
            "CLICKHOUSE_USER": os.environ["CLICKHOUSE_USER"],
            "CLICKHOUSE_PASSWORD": os.environ["CLICKHOUSE_PASSWORD"],
            "CLICKHOUSE_DATABASE": os.getenv("CLICKHOUSE_DATABASE", "slatesafe"),
            "CLICKHOUSE_SECURE": os.getenv("CLICKHOUSE_SECURE", "true"),
            "CLICKHOUSE_VERIFY": os.getenv("CLICKHOUSE_VERIFY", "true"),
            "CLICKHOUSE_ALLOW_WRITE_ACCESS": "false",
        }

    async def query(self, sql: str) -> str:
        """Execute a read-only query through ClickHouse's official MCP server."""
        params = StdioServerParameters(
            command=os.getenv("MCP_CLICKHOUSE_BINARY", "mcp-clickhouse"),
            args=[],
            env=self._env(),
        )
        async with AsyncExitStack() as stack:
            read, write = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            result = await session.call_tool("run_query", {"query": sql})
            return "\n".join(getattr(block, "text", str(block)) for block in result.content)

    async def rights_window(self, asset_ids: list[str], territory: str, release_date: str) -> str:
        """Return all ledger records so policy can explain a failed condition exactly."""
        quoted_assets = ", ".join("'{}'".format(asset.replace("'", "''")) for asset in asset_ids)
        return await self.query(
            "SELECT asset_id, category, territories, expires_at, release_date, evidence_url "
            "FROM clearance_events "
            f"WHERE asset_id IN ({quoted_assets}) "
            "ORDER BY asset_id, expires_at DESC"
        )
