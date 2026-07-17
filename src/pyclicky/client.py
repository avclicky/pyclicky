from __future__ import annotations

from typing import Any, Self, Optional, Type
from types import TracebackType

import aiohttp


class ClickyAPIError(Exception):
    """Raised when the Clicky API returns an error."""


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
    ) -> Any:
        """
        Generic API request.

        Example:
            await client.query(
                "visitors",
                date="today",
            )
        """

        query = {
            "site_id": self.site_id,
            "sitekey": self.sitekey,
            "type": report_type,
            "output": "json",
            **params,
        }

        async with self.session.get(self.BASE_URL, params=query) as resp:
            resp.raise_for_status()

            data = await resp.json(content_type=None)

            # Clicky returns API errors inside the JSON payload.
            if (
                isinstance(data, list)
                and data
                and isinstance(data[0], dict)
                and "error" in data[0]
            ):
                raise ClickyAPIError(data[0]["error"])

            return data

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    async def visitors(self, **kwargs: Any) -> Any:
        return await self.query("visitors", **kwargs)

    async def actions(self, **kwargs: Any) -> Any:
        return await self.query("actions", **kwargs)

    async def pages(self, **kwargs: Any) -> Any:
        return await self.query("pages", **kwargs)

    async def downloads(self, **kwargs: Any) -> Any:
        return await self.query("downloads", **kwargs)

    async def searches(self, **kwargs: Any) -> Any:
        return await self.query("searches", **kwargs)

    async def links(self, **kwargs: Any) -> Any:
        return await self.query("links", **kwargs)

    async def countries(self, **kwargs: Any) -> Any:
        return await self.query("countries", **kwargs)

    async def visitors_list(self, **kwargs: Any) -> Any:
        return await self.query("visitors-list", **kwargs)

    async def actions_list(self, **kwargs: Any) -> Any:
        return await self.query("actions-list", **kwargs)

    async def goals(self, **kwargs: Any) -> Any:
        return await self.query("goals", **kwargs)
