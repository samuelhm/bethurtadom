from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, Page

from src.core.logger import logger


class BrowserManager:
    """Gestiona el ciclo de vida del navegador con Camoufox para máxima invisibilidad."""

    def __init__(self, headless: bool = False) -> None:
        self.headless = headless
        self._camoufox: AsyncCamoufox | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    async def start(self) -> None:
        """Inicia Camoufox y prepara la página inicial."""
        if not self._browser:
            try:
                logger.info("🦊 Lanzando Camoufox (Base Sólida v0.4.11)...")

                self._camoufox = AsyncCamoufox(
                    headless=self.headless,
                    os="windows",
                    geoip=True,
                    humanize=True,
                )

                # Camoufox.start() devuelve un objeto Browser en tiempo de ejecución.
                # Añadimos type: ignore para evitar que Pylance marque un error falso de tipado.
                self._browser = await self._camoufox.start()  # type: ignore

                if self._browser:
                    # Creamos un contexto limpio
                    context = await self._browser.new_context()
                    self._page = await context.new_page()
                    logger.info("✅ Camoufox iniciado: Navegador y página listos.")
                else:
                    logger.error("❌ El motor de Camoufox no devolvió un navegador válido.")

            except Exception as e:
                logger.error(f"❌ Error crítico al iniciar el navegador: {e}")
                self._browser = None
                self._page = None
                raise

    async def get_new_page(self) -> Page:
        """Devuelve la página activa de Camoufox."""
        if not self._page:
            await self.start()

        if not self._page:
            raise RuntimeError("No se pudo obtener la página del navegador.")

        return self._page

    async def stop(self) -> None:
        """Cierra el navegador y limpia los recursos."""
        logger.debug("BrowserManager: Cerrando recursos...")
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.debug(f"Error silencioso al cerrar el navegador: {e}")
            finally:
                self._browser = None
                self._page = None
