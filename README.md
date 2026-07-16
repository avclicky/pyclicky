# pyclicky

Async Python client for the Clicky Analytics API.

## Installation

```bash
pip install pyclicky
```

## Example

```python
import asyncio
from pyclicky import ClickyClient

async def main():
    async with ClickyClient(
        site_id=12345,
        sitekey="your_sitekey",
    ) as client:

        visitors = await client.visitors(date="today")
        print(visitors)

asyncio.run(main())
```

## Generic Queries

```python
await client.query(
    "pages",
    date="last-30-days",
    limit=25,
)
```

Supports every Clicky report type via `query()`.
