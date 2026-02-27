from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, Page

from src.core.logger import logger


class BrowserManager:
    """Navegador indetectable usando Camoufox (Firefox-based advanced stealth)."""

    def __init__(self, headless: bool = False) -> None:
        self.headless = headless
        self._camoufox: AsyncCamoufox | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    async def start(self) -> None:
        """Lanza Camoufox con configuración optimizada para evasión de anti-bots."""
        if not self._browser:
            try:
                logger.info("🦊 Lanzando Camoufox (API 0.4.11)...")
                
                # Inicializamos Camoufox con geoip=True para sincronización automática
                self._camoufox = AsyncCamoufox(
                    headless=self.headless,
                    os="windows",
                    # geoip=True detecta tu IP y ajusta locale/timezone automáticamente
                    geoip=True,
                    # humanize añade movimientos de ratón realistas
                    humanize=True,
                )
                
                # Iniciamos el navegador y obtenemos el objeto Browser
                self._browser = await self._camoufox.start()
                
                if self._browser:
                    # Abrimos la página directamente desde el browser
                    self._page = await self._browser.new_page()
                    logger.info("✅ Camoufox se ha iniciado correctamente con GeoIP y Humanize.")
                else:
                    logger.error("❌ El motor de Camoufox no devolvió un objeto Browser.")
                    
            except Exception as e:
                logger.error(f"❌ Error crítico al iniciar Camoufox: {e}")
                self._camoufox = None
                self._browser = None
                self._page = None
                raise

    async def get_new_page(self) -> Page:
        """Devuelve la página principal de Camoufox."""
        if not self._page:
            await self.start()

        if not self._page:
            raise RuntimeError("No se pudo obtener la página de Camoufox.")
        
        return self._page

    async def stop(self) -> None:
        """Cierra el navegador y limpia recursos."""
        logger.debug("BrowserManager: Cerrando...")
        if self._browser:
            await self._browser.close()
