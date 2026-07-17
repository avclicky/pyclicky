"""Tests for pyclicky."""

import pytest

from datetime import date
from pyclicky import ClickyClient


@pytest.mark.asyncio
async def test_client_creation() -> None:
    async with ClickyClient("1", "abc") as client:
        assert client.site_id == "1"
        assert client.sitekey == "abc"


@pytest.mark.asyncio
async def test_client_serializer() -> None:
    async with ClickyClient(32020, "cda1dc5da3c144f4") as client:
        visitors_text_date = await client.visitors(date="today")
        visitors_date_date = await client.visitors(date=date.today())
        assert visitors_text_date == visitors_date_date
