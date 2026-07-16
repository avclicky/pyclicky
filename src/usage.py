import asyncio
from pyclicky import ClickyClient

async def main():
    async with ClickyClient(
        site_id=32020,
        sitekey="cda1dc5da3c144f4",
    ) as client:

        visitors = await client.visitors(date="today")
        print(visitors)

        pages = await client.pages(
            date="last-7-days",
            limit=20,
        )
        print(pages)

        searches = await client.searches(
            date="yesterday",
        )
        print(searches)

asyncio.run(main())
