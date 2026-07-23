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

## Development environment

```sh
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -e .

# Run pre-commit
python -m pip install pre-commit
pre-commit install
pre-commit run --all-files

# Run tests
python -m pip install -e ".[test]"
pytest

# Build package
python -m pip install build
python -m build
```
