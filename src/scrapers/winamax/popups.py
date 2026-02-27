import contextlib

from playwright.async_api import Page


async def handle_popups(page: Page) -> None:
    with contextlib.suppress(Exception):
        await page.click("#tarteaucitronPersonalize2", timeout=2000)

    with contextlib.suppress(Exception):
        await page.mouse.click(10, 10)
