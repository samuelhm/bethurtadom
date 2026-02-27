import os
import asyncio
from pathlib import Path

from src.core.browser import BrowserManager
from src.core.logger import logger
from src.models.odds import MatchInfo
from src.scrapers.base import BaseScraper


class Bet365Scraper(BaseScraper):
    """Implementa el scraper para Bet365 con soporte para carga dinámica (scroll)."""

    def __init__(self, browser_manager: BrowserManager) -> None:
        self.browser_manager = browser_manager
        self._page = None
        self._live_url = "https://www.bet365.es/#/IP/B1"
        self._username = os.getenv("BET365_USER")
        self._password = os.getenv("BET365_PASS")

        self._js_path = Path(__file__).parent / "match_selector.js"
        self._selector_script = self._js_path.read_text(encoding="utf-8")

    async def start(self) -> bool:
        """Inicializa el navegador, navega y hace scroll para cargar todos los partidos."""
        try:
            if not self._page:
                self._page = await self.browser_manager.get_new_page()

            logger.info(f"🚀 Cargando Bet365 En Vivo: {self._live_url}")
            await self._page.goto(self._live_url, wait_until="networkidle")
            
            # Esperamos al contenedor principal
            await self._page.wait_for_selector('.ovm-CompetitionList', timeout=20000)
            
            # --- TÉCNICA DE AUTO-SCROLL ---
            logger.info("🖱️ Realizando scroll para cargar todos los partidos...")
            for _ in range(5): # Hacemos 5 scrolls para cubrir la mayoría de ligas
                await self._page.mouse.wheel(0, 2000)
                await asyncio.sleep(1) # Esperamos a que el JS cargue los datos
            
            # Volvemos arriba para que la extracción sea limpia (opcional)
            await self._page.mouse.wheel(0, -10000)
            await asyncio.sleep(0.5)
            
            return True
        except Exception as e:
            logger.error(f"Error al iniciar Bet365: {e}")
            return False

    async def login(self) -> bool:
        return False

    async def navigate_to_live(self) -> bool:
        return True

    async def get_live_matches(self) -> list[MatchInfo]:
        """Extrae los partidos usando el script JS."""
        if not self._page:
            return []
        try:
            # Re-ejecutamos el script de extracción
            matches_data = await self._page.evaluate(self._selector_script)
            return [MatchInfo(**m) for m in matches_data]
        except Exception as e:
            logger.error(f"Error en extracción Bet365: {e}")
            return []

    async def close(self) -> None:
        if self._page:
            await self._page.close()
