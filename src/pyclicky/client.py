"""Async client for the Clicky Web Analytics API."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from types import TracebackType
from typing import Any, Optional, Self, Type

import aiohttp
from aiohttp import ClientConnectorError

from .exceptions import (
    ClickyAPIError,
    AuthenticationError,
    InvalidEndpoint,
    ConnectionError,
    ServiceUnavailable,
)


def _serialize(value: Any) -> str | int | float:
    """Convert Python objects into Clicky API query parameters."""

    if isinstance(value, StrEnum):
        return value

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, (str, int, float)):
        return value

    raise TypeError(f"Unsupported query parameter type: {type(value).__name__}")


def _coerce(value: Any) -> Any:
    """Turn Clicky's stringly-typed item values into real Python types."""

    if not isinstance(value, str):
        return value

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


@dataclass(frozen=True, slots=True)
class ReportItem:
    """A single row within a date bucket (one page, one country, one goal, ...)."""

    title: str | None
    value: Any
    value_percent: float | None = None
    url: str | None = None
    stats_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def _from_raw(cls, raw: dict[str, Any]) -> Self:
        known = {"title", "value", "value_percent", "url", "stats_url"}
        return cls(
            title=raw.get("title"),
            value=_coerce(raw.get("value")),
            value_percent=(
                float(raw["value_percent"]) if "value_percent" in raw else None
            ),
            url=raw.get("url"),
            stats_url=raw.get("stats_url"),
            extra={k: _coerce(v) for k, v in raw.items() if k not in known},
        )


@dataclass(frozen=True, slots=True)
class ReportDate:
    """All items Clicky returned for a single day, or a whole date range."""

    start: date
    end: date
    items: list[ReportItem]

    @classmethod
    def _from_raw(cls, raw: dict[str, Any]) -> Self:
        start_str, _, end_str = raw["date"].partition(",")
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else start

        return cls(
            start=start,
            end=end,
            items=[ReportItem._from_raw(item) for item in raw.get("items", [])],
        )

    @property
    def date(self) -> date:
        """Convenience accessor for the common case where start == end."""
        return self.start


@dataclass(frozen=True, slots=True)
class Report:
    """A fully-parsed Clicky report, independent of the API's nested wire format."""

    type: str
    dates: list[ReportDate]

    @classmethod
    def _from_raw(cls, raw: dict[str, Any]) -> Self:
        return cls(
            type=raw["type"],
            dates=[ReportDate._from_raw(d) for d in raw.get("dates", [])],
        )

    @property
    def items(self) -> list[ReportItem]:
        """Items for the (common) single-date case, without digging into `.dates`."""
        return self.dates[0].items if self.dates else []

    @property
    def value(self) -> Any:
        """The single value for tally-style reports (visitors, actions, ...)."""
        items = self.items
        return items[0].value if items else None


class ClickyClient:
    BASE_URL = "https://api.clicky.com/api/stats/4"

    def __init__(
        self,
        site_id: str | int,
        sitekey: str,
        *,
        session: aiohttp.ClientSession | None = None,
        timeout: float = 30,
    ) -> None:
        self.site_id = str(site_id)
        self.sitekey = sitekey

        self._external_session = session is not None
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def __aenter__(self) -> Self:
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        if not self._external_session and self._session:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError(
                "ClientSession not initialized. "
                "Use 'async with ClickyClient(...)' or pass a session."
            )
        return self._session

    async def query(
        self,
        report_type: str,
        **params: Any,
    ) -> Report:
        """
        Generic API request, returning a typed `Report` rather than Clicky's
        raw `[{"type": ..., "dates": [{"date": ..., "items": [...]}]}]` payload.

        Example:
            report = await client.query("visitors", date="today")
            report.value          # tally reports
            report.items          # list-style reports
        """

        query: dict[str, Any] = {
            "site_id": self.site_id,
            "sitekey": self.sitekey,
            "type": report_type,
            "output": "json",
        }
        query.update(
            {
                key: _serialize(value)
                for key, value in params.items()
                if value is not None
            }
        )

        try:
            async with self.session.get(self.BASE_URL, params=query) as resp:
                # Handle explicit HTTP status codes
                # Clicky's API does not change HTTP status codes explicitly, but
                # their server infrastructure can produce 503s.
                if resp.status == 503:
                    raise ServiceUnavailable()

                if resp.status == 404:
                    raise InvalidEndpoint()

                resp.raise_for_status()

                data = await resp.json(content_type=None)
        except ClientConnectorError as e:
            raise ConnectionError(e)

        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            raise ClickyAPIError(f"Unexpected response payload: {data!r}")

        payload = data[0]

        # Clicky returns API errors inside the JSON payload.
        if "error" in payload:
            if payload["error"] == "Invalid sitekey.":
                raise AuthenticationError()

            raise ClickyAPIError(payload["error"])

        return Report._from_raw(payload)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    async def visitors(self, **kwargs: Any) -> Report:
        return await self.query("visitors", **kwargs)

    async def actions(self, **kwargs: Any) -> Report:
        return await self.query("actions", **kwargs)

    async def pages(self, **kwargs: Any) -> Report:
        return await self.query("pages", **kwargs)

    async def downloads(self, **kwargs: Any) -> Report:
        return await self.query("downloads", **kwargs)

    async def searches(self, **kwargs: Any) -> Report:
        return await self.query("searches", **kwargs)

    async def links(self, **kwargs: Any) -> Report:
        return await self.query("links", **kwargs)

    async def countries(self, **kwargs: Any) -> Report:
        return await self.query("countries", **kwargs)

    async def time_total(self, **kwargs: Any) -> Report:
        return await self.query("time-total", **kwargs)

    async def visitors_list(self, **kwargs: Any) -> Report:
        return await self.query("visitors-list", **kwargs)

    async def visitors_online(self, **kwargs: Any) -> Report:
        return await self.query("visitors-online", **kwargs)

    async def actions_list(self, **kwargs: Any) -> Report:
        return await self.query("actions-list", **kwargs)

    async def goals(self, **kwargs: Any) -> Report:
        return await self.query("goals", **kwargs)
