import os

from src.core.browser import BrowserManager
from src.models.odds import ScrapedData
from src.scrapers.base import BaseScraper
from src.scrapers.winamax.auth import login_winamax
from src.scrapers.winamax.navigation import go_to_live_football
from src.scrapers.winamax.pages import handle_popups


class WinamaxScraper(BaseScraper):
    """Scraper de Winamax modularizado."""

    def __init__(self, browser_manager: BrowserManager) -> None:
        """Inicializa el scraper."""
        self.browser_manager = browser_manager
        # La serialización de Playwright falla si se envían objetos no serializables a sus métodos.
        self._page = None
        self._base_url = "https://www.winamax.es/apuestas-deportivas"
        self._username = os.getenv("WINAMAX_USER")
        self._password = os.getenv("WINAMAX_PASS")
        self._birthday = os.getenv("WINAMAX_BIRTHDAY")
        self._inspect_mode = os.getenv("WINAMAX_INSPECT", "0") == "1"

    async def login(self) -> bool:
        """Orquesta el proceso de login y navegación."""
        try:
            if not self._username or not self._password or not self._birthday:
                print("❌ Error: Faltan credenciales de Winamax en .env")
                return False

            # Configuración inicial de la página
            self._page = await self.browser_manager.get_new_page()

            print(f"🌐 Navegando a {self._base_url}...")
            # Usamos 'load' para evitar problemas de red infinita y serialización
            await self._page.goto(str(self._base_url), wait_until="load")
            await handle_popups(self._page)

            # Autenticación
            if not await login_winamax(self._page, self._username, self._password, self._birthday):
                return False

            # Navegación a sección objetivo
            return await go_to_live_football(
                self._page, self._base_url, inspect_mode=self._inspect_mode
            )

        except Exception as e:
            print(f"❌ Error crítico en WinamaxScraper.login: {e}")
            return False

    async def get_live_matches(self) -> list[ScrapedData]:
        """Placeholder para la extracción de partidos en vivo."""
        return []

    async def close(self) -> None:
        """Limpia recursos."""
        if self._page:
            await self._page.close()
