import os
from pathlib import Path

from src.core.browser import BrowserManager
from src.core.logger import logger
from src.models.odds import MatchInfo
from src.scrapers.base import BaseScraper
from src.scrapers.bet365.auth import login_bet365
from src.scrapers.bet365.popups import handle_cookie_btn


class Bet365Scraper(BaseScraper):
    logger.debug("Inicializando Bet365Scraper...")
    def __init__(self, browser_manager: BrowserManager) -> None:
        self.browser_manager = browser_manager
        self._page = None
        self._base_url = "https://www.bet365.es/#/IP/POP"
        self._username = os.getenv("BET365_USER")
        self._password = os.getenv("BET365_PASS")

        self._js_path = Path(__file__).parent / "match_selector.js"
        self._selector_script = self._js_path.read_text(encoding="utf-8")

    async def start(self) -> bool:
        try:
            if not self._page:
                logger.debug("Bet365Scraper.start: Requesting new page from BrowserManager")
                self._page = await self.browser_manager.get_new_page()

            logger.info(f"🌐 Navegando a {self._base_url}...")
            await self._page.goto(str(self._base_url), wait_until="networkidle")

            logger.debug("Bet365Scraper.start: Calling handle_cookie_btn() to clean UI")
            await handle_cookie_btn(self._page)
            return True

        except Exception as e:
            logger.error(f"Error al iniciar el scraper: {e}")
            return False

    async def login(self) -> bool:
        if not self._page:
            logger.error("Bet365Scraper.navigate_to_live: Aborting. self._page is None.")
            return False
        try:
            if not self._username or not self._password:
                logger.error("Bet365Scraper.navigate_to_live: Aborting. Missing credentials in environment.")
                return False

            logger.info("🔐 Iniciando sesión en Bet365...")
            logger.debug(
                f"Bet365Scraper.navigate_to_live: Calling login_bet365() with user={self._username}"
            )
            if not await login_bet365(self._page, self._username, self._password):
                return False

            logger.debug(
                "Bet365Scraper.navigate_to_live: Calling go_to_live_bet365() after successful login"
            )
            return True
        except Exception as e:
            logger.error(f"Error crítico en Bet365Scraper.navigate_to_live: {e}")
            return False

    async def select_football(self) -> bool:
        if not self._page:
            logger.error("Bet365Scraper.select_football: Aborting. self._page is None.")
            return False
        try:
            logger.info("🚀 Navegando a la sección En Vivo de Bet365...")
            ballbutton = self._page.locator("a.ovm-ClassificationBarButton-1")
            await ballbutton.click(timeout=200)
            return True
        except Exception as e:
            logger.error(f"Error crítico en Bet365Scraper.select_football: {e}")
            return False

    async def get_live_matches(self) -> list[MatchInfo]:
        return []

    async def close(self) -> None:
        if self._page:
            await self._page.close()

