import pytest

from pyclicky import ClickyClient


@pytest.mark.asyncio
async def test_client_creation() -> None:
    async with ClickyClient("1", "abc") as client:
        assert client.site_id == "1"
        assert client.sitekey == "abc"
