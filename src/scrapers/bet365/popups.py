import contextlib
from src.core.logger import logger
from playwright.async_api import Page


async def handle_cookie_btn(page: Page) -> None:
    boton_cookies = page.get_by_role("button", name="Aceptar todo")
    with contextlib.suppress(Exception):
        await boton_cookies.click(timeout=1000)
        logger.info("Popup de cookies cerrado")
    return
