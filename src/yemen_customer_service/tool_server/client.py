"""Trusted MCP adapter; this module does not implement an LLM loop.

Wire references stay here, outside the schemas/results returned to future models.
The server still authorizes every call independently.
"""

from __future__ import annotations

import asyncio
import copy
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import anyio
from jsonschema import Draft202012Validator
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from yemen_customer_service.storage.store import Store, payload_hash
from yemen_customer_service.tool_server.models import SafeError, TicketDraft

PRIVATE_FIELDS = {"access_reference", "confirmation_reference"}


@asynccontextmanager
async def protocol_session(parameters: StdioServerParameters) -> AsyncIterator[ClientSession]:
    """Drain late responses only during intentional SDK subprocess shutdown.

    SDK 1.30's stdio reader can race a closed session after a timed-out call.
    Give the session cloned streams and keep the transport receiver alive until
    the server exits. No tool result is fabricated or accepted by this drain.
    """
    drain = None

    async def discard_late_messages(read):
        try:
            async for _ in read:
                pass
        except (anyio.ClosedResourceError, anyio.EndOfStream):
            pass

    try:
        async with stdio_client(parameters) as (read, write):
            try:
                async with ClientSession(read.clone(), write.clone()) as session:
                    await session.initialize()
                    yield session
            finally:
                drain = asyncio.create_task(discard_late_messages(read))
    finally:
        if drain is not None:
            drain.cancel()
            try:
                await drain
            except asyncio.CancelledError:
                pass


class TrustedClient:
    def __init__(self, session: ClientSession, store: Store, token: str | None):
        self._session = session
        self._store = store
        self._token = token
        self._access: dict[str, str] = {}
        self._confirmation: tuple[str, str] | None = None

    async def tools_for_model(self) -> list[dict[str, Any]]:
        tools = []
        for tool in (await self._session.list_tools()).tools:
            schema = copy.deepcopy(tool.inputSchema)
            for key in PRIVATE_FIELDS:
                schema["properties"].pop(key, None)
            schema["required"] = [
                key for key in schema.get("required", []) if key not in PRIVATE_FIELDS
            ]
            # Expose only safe inputs, not wire output schemas containing references.
            tools.append(
                {"name": tool.name, "description": tool.description, "inputSchema": schema}
            )
        return tools

    def confirm_ticket(self, draft: TicketDraft, *, confirmed: bool) -> None:
        """Trusted UI/console entry point. Never register it as an LLM or MCP tool."""
        self._confirmation = None
        if not self._token:
            raise SafeError("ACCESS_DENIED")
        reference = self._store.register_confirmation(self._token, draft, confirmed=confirmed)
        self._confirmation = (payload_hash(draft), reference)

    def cancel_ticket(self) -> None:
        """Trusted UI must call on every draft edit or cancellation."""
        self._confirmation = None
        if self._token:
            self._store.revoke_confirmations(self._token)

    async def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        definitions = {tool["name"]: tool for tool in await self.tools_for_model()}
        if name not in definitions:
            raise SafeError("UNKNOWN_TOOL")
        if PRIVATE_FIELDS.intersection(arguments) or not Draft202012Validator(
            definitions[name]["inputSchema"]
        ).is_valid(arguments):
            raise SafeError("INVALID_INPUT")
        wire = copy.deepcopy(arguments)
        if name in {"get_order_status", "create_support_ticket"} and wire.get("order_id"):
            reference = self._access.get(wire["order_id"])
            if reference is None:
                raise SafeError("ACCESS_DENIED")
            wire["access_reference"] = reference
        if name == "create_support_ticket":
            draft = TicketDraft.model_validate(arguments)
            if not self._confirmation or self._confirmation[0] != payload_hash(draft):
                self.cancel_ticket()
                raise SafeError("CONFIRMATION_REQUIRED")
            wire["confirmation_reference"] = self._confirmation[1]
        response = await self._session.call_tool(name, wire)
        body = copy.deepcopy(response.structuredContent)
        if body is None:
            raise SafeError("INTERNAL_ERROR")
        if name == "verify_order_access" and not response.isError:
            reference = body["data"].pop("access_reference")
            self._access[arguments["order_id"]] = reference
        return body


@asynccontextmanager
async def connect(
    database_path: str | Path,
    store: Store,
    token: str | None = None,
    *,
    enable_demo_auth: bool = False,
    enable_hosted_auth: bool = False,
) -> AsyncIterator[TrustedClient]:
    """Launch one real stdio MCP server bound to one trusted synthetic session."""
    app_env = os.getenv("APP_ENV", "development")
    if app_env == "production":
        from yemen_customer_service.hosting.store import HostedStore

        if (
            not enable_hosted_auth
            or enable_demo_auth
            or not isinstance(store, HostedStore)
            or not token
        ):
            raise SafeError("ACCESS_DENIED")
        with store.db.connect() as conn:
            store.session(conn, token)  # Bound to a live, invited, unrevoked login.
    elif token and (not enable_demo_auth or app_env != "development" or enable_hosted_auth):
        raise SafeError("ACCESS_DENIED")
    env = {
        "DATABASE_PATH": str(Path(database_path).resolve()),
        "APP_ENV": app_env,
        "ENABLE_DEMO_AUTH": "true" if enable_demo_auth else "false",
        "HOSTED_MODE": "true" if enable_hosted_auth else "false",
    }
    if token:
        env["CS_SESSION_TOKEN"] = token
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "yemen_customer_service.tool_server.server"],
        env=env,
    )
    async with protocol_session(params) as session:
        yield TrustedClient(session, store, token)
