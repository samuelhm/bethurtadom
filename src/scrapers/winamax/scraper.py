import os
import asyncio
from pathlib import Path

from src.core.browser import BrowserManager
from src.core.logger import logger
from src.models.odds import MatchInfo
from src.scrapers.base import BaseScraper
from src.scrapers.winamax.auth import login_winamax
from src.scrapers.winamax.popups import handle_popups


class WinamaxScraper(BaseScraper):
    """Scraper original restaurado con navegación directa."""

    def __init__(self, browser_manager: BrowserManager) -> None:
        self.browser_manager = browser_manager
        self._page = None
        self._base_url = "https://www.winamax.es/apuestas-deportivas/live"
        self._username = os.getenv("WINAMAX_USER")
        self._password = os.getenv("WINAMAX_PASS")
        self._birthday = os.getenv("WINAMAX_BIRTHDAY")

        self._js_path = Path(__file__).parent / "match_selector.js"
        self._selector_script = self._js_path.read_text(encoding="utf-8")

    async def start(self) -> bool:
        try:
            if not self._page:
                self._page = await self.browser_manager.get_new_page()

            logger.info(f"🌐 Navegando a Winamax Live: {self._base_url}")
            await self._page.goto(str(self._base_url), wait_until="networkidle")
            await handle_popups(self._page)
            return True
        except Exception as e:
            logger.error(f"Error al iniciar: {e}")
            return False

    async def login(self) -> bool:
        if not self._page: return False
        try:
            if not self._username or not self._password or not self._birthday:
                return False
            logger.info("🔐 Iniciando sesión...")
            await login_winamax(self._page, self._username, self._password, self._birthday)
            await handle_popups(self._page)
            return True
        except Exception:
            return False

    async def navigate_to_live(self) -> bool:
        if not self._page: return False
        try:
            # Restauramos el click directo en el botón de Fútbol de la barra lateral/superior
            logger.info("⚽ Seleccionando filtro de fútbol...")
            await self._page.get_by_role("button", name="Fútbol").first.click()
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Error al navegar a fútbol: {e}")
            return False

    async def get_live_matches(self) -> list[MatchInfo]:
        if not self._page: return []
        try:
            await self._page.wait_for_selector('[data-testid^="match-card-"]', timeout=10000)
            matches_data = await self._page.eval_on_selector_all(
                '[data-testid^="match-card-"]',
                self._selector_script
            )
            return [MatchInfo(**m) for m in matches_data]
        except Exception as e:
            logger.error(f"Error en extracción: {e}")
            return []

    async def close(self) -> None:
        if self._page: await self._page.close()
