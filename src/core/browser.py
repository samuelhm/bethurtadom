from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, Page

from src.core.logger import logger


class BrowserManager:
    """Gestiona el ciclo de vida del navegador con Camoufox y configuración estándar."""

    def __init__(self, headless: bool = False) -> None:
        self.headless = headless
        self._camoufox: AsyncCamoufox | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    async def start(self) -> None:
        """Inicia Camoufox con resolución estándar humana."""
        if not self._browser:
            try:
                logger.info("🦊 Lanzando Camoufox (Resolución Estándar)...")

                self._camoufox = AsyncCamoufox(
                    headless=self.headless,
                    os="windows",
                    geoip=True,
                    humanize=True,
                )

                self._browser = await self._camoufox.start()  # type: ignore

                if self._browser:
                    # Usamos una resolución estándar de 1080p
                    context = await self._browser.new_context(
                        viewport={"width": 1920, "height": 1080}
                    )
                    self._page = await context.new_page()
                    logger.info("✅ Camoufox iniciado correctamente.")
                else:
                    logger.error("❌ El motor de Camoufox no devolvió un navegador válido.")

            except Exception as e:
                logger.error(f"❌ Error crítico al iniciar el navegador: {e}")
                self._browser = None
                self._page = None
                raise

    async def get_new_page(self) -> Page:
        """Devuelve la página activa."""
        if not self._page:
            await self.start()
        return self._page

    async def stop(self) -> None:
        """Cierra el navegador."""
        logger.debug("BrowserManager: Cerrando recursos...")
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None
