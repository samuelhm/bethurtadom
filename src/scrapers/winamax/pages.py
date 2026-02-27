import contextlib

from playwright.async_api import Page


async def handle_popups(page: Page) -> None:
    """Cierra banners iniciales y clics de cortesía para limpiar la vista."""
    # Botón de cookies si aparece
    with contextlib.suppress(Exception):
        await page.click("#tarteaucitronPersonalize2", timeout=2000)

    # Clic en una zona vacía para cerrar cualquier overlay residual
    with contextlib.suppress(Exception):
        await page.mouse.click(10, 10)
