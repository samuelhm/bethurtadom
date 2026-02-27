import os
from pathlib import Path

from src.core.browser import BrowserManager
from src.core.logger import logger
from src.models.odds import MatchInfo
from src.scrapers.base import BaseScraper
from src.scrapers.winamax.auth import login_winamax
from src.scrapers.winamax.navigation import go_to_live_football
from src.scrapers.winamax.popups import handle_popups


class WinamaxScraper(BaseScraper):
    logger.debug("Inicializando WinamaxScraper...")

    def __init__(self, browser_manager: BrowserManager) -> None:
        self.browser_manager = browser_manager
        self._page = None
        self._base_url = "https://www.winamax.es/apuestas-deportivas"
        self._username = os.getenv("WINAMAX_USER")
        self._password = os.getenv("WINAMAX_PASS")
        self._birthday = os.getenv("WINAMAX_BIRTHDAY")

        logger.debug("Cargando script de extracción de partidos desde match_selector.js...")
        self._js_path = Path(__file__).parent / "match_selector.js"
        self._selector_script = self._js_path.read_text(encoding="utf-8")

    async def start(self) -> bool:
        try:
            if not self._page:
                logger.debug("WinamaxScraper.start: Requesting new page from BrowserManager")
                self._page = await self.browser_manager.get_new_page()

            logger.info(f"🌐 Navegando a {self._base_url}...")
            await self._page.goto(str(self._base_url), wait_until="networkidle")

            logger.debug("WinamaxScraper.start: Calling handle_popups() to clean UI")
            await handle_popups(self._page)
            return True

        except Exception as e:
            logger.error(f"Error al iniciar el scraper: {e}")
            return False

    async def login(self) -> bool:
        if not self._page:
            logger.error("WinamaxScraper.login: Aborting. self._page is None.")
            return False

        try:
            if not self._username or not self._password or not self._birthday:
                logger.error("WinamaxScraper.login: Aborting. Missing credentials in environment.")
                return False

            logger.info("🔐 Iniciando sesión en Winamax...")
            logger.debug(
                f"WinamaxScraper.login: Calling login_winamax() with user={self._username}"
            )
            if not await login_winamax(self._page, self._username, self._password, self._birthday):
                return False

            logger.debug(
                "WinamaxScraper.login: Calling go_to_live_football() after successful login"
            )
            await handle_popups(self._page)
            return True

        except Exception as e:
            logger.error(f"Error crítico en WinamaxScraper.login: {e}")
            return False

    async def navigate_to_live(self) -> bool:
        if not self._page:
            logger.error("WinamaxScraper.navigate_to_live: Aborting. self._page is None.")
            return False

        logger.debug("WinamaxScraper.navigate_to_live: Calling go_to_live_football()")
        return await go_to_live_football(self._page, self._base_url)

    async def get_live_matches(self) -> list[MatchInfo]:
        logger.debug("WinamaxScraper.get_live_matches: Starting extraction of live matches")
        if not self._page:
            logger.error("WinamaxScraper.get_live_matches: Aborting. self._page is None.")
            return []

        try:
            logger.debug(
                "WinamaxScraper.get_live_matches: Waiting for '[data-testid^=\"match-card-\"]' selector"
            )
            await self._page.wait_for_selector('[data-testid^="match-card-"]', timeout=10000)

            logger.debug(
                "WinamaxScraper.get_live_matches: Executing eval_on_selector_all with pre-loaded JS script"
            )
            matches_data = await self._page.eval_on_selector_all(
                '[data-testid^="match-card-"]', self._selector_script
            )

            logger.debug(
                f"WinamaxScraper.get_live_matches: Mapping {len(matches_data)} items to MatchInfo models"
            )
            return [MatchInfo(**m) for m in matches_data]

        except Exception as e:
            logger.error(f"Error al extraer partidos en vivo: {e}")
            return []

    async def close(self) -> None:
        if self._page:
            await self._page.close()
