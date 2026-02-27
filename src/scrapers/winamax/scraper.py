import os

from src.core.browser import BrowserManager
from src.core.logger import logger
from src.models.odds import MatchInfo, ScrapedData
from src.scrapers.base import BaseScraper
from src.scrapers.winamax.auth import login_winamax
from src.scrapers.winamax.navigation import go_to_live_football
from src.scrapers.winamax.pages import handle_popups


class WinamaxScraper(BaseScraper):
    """Scraper de Winamax modularizado."""

    def __init__(self, browser_manager: BrowserManager) -> None:
        self.browser_manager = browser_manager
        self._page = None
        self._base_url = "https://www.winamax.es/apuestas-deportivas"
        self._username = os.getenv("WINAMAX_USER")
        self._password = os.getenv("WINAMAX_PASS")
        self._birthday = os.getenv("WINAMAX_BIRTHDAY")

    async def start(self) -> bool:
        """Prepara el navegador y navega a la web de Winamax."""
        try:
            if not self._page:
                self._page = await self.browser_manager.get_new_page()

            logger.info(f"🌐 Navegando a {self._base_url}...")
            await self._page.goto(str(self._base_url), wait_until="load")
            await handle_popups(self._page)
            return True
        except Exception as e:
            logger.error(f"Error al iniciar el scraper: {e}")
            return False

    async def login(self) -> bool:
        """Realiza el proceso de login (requiere haber llamado a start() antes)."""
        if not self._page:
            logger.error("Error: No se ha inicializado el navegador. Llama a start() primero.")
            return False

        try:
            if not self._username or not self._password or not self._birthday:
                logger.error("Faltan credenciales de Winamax en .env")
                return False

            logger.info("🔐 Iniciando sesión en Winamax...")
            if not await login_winamax(self._page, self._username, self._password, self._birthday):
                return False

            return await go_to_live_football(self._page, self._base_url)

        except Exception as e:
            logger.error(f"Error crítico en WinamaxScraper.login: {e}")
            return False

    async def navigate_to_live(self) -> bool:
        """Navega directamente a la sección en vivo sin loguearse."""
        if not self._page:
            logger.error("Error: No se ha inicializado el navegador. Llama a start() primero.")
            return False
        return await go_to_live_football(self._page, self._base_url)

    async def get_live_matches(self) -> list[MatchInfo]:
        """Extrae la información básica de los partidos de fútbol en vivo."""
        if not self._page:
            return []

        try:
            container_selector = ".ReactVirtualized__Grid__innerScrollContainer"
            
            # Esperamos un poco más a que la red se estabilice tras el filtro
            await self._page.wait_for_timeout(2000)
            
            try:
                await self._page.wait_for_selector(container_selector, timeout=10000)
            except Exception:
                logger.warning("No se encontró el contenedor de la lista virtualizada.")
                return []

            # Debug: ¿Cuántos divs hijos hay realmente?
            num_elements = await self._page.locator(f"{container_selector} > div").count()
            logger.info(f"Detectados {num_elements} bloques de partidos en el DOM.")

            matches_data = await self._page.eval_on_selector_all(
                f"{container_selector} > div",
                r"""
                (elements) => {
                    return elements.map(el => {
                        // Nombres de equipos: específicos de fútbol (.sc-gbWBZM)
                        const teamElements = Array.from(el.querySelectorAll('.sc-gbWBZM'));
                        if (teamElements.length < 2) return null;
                        
                        const homeTeam = teamElements[0].innerText.trim();
                        const awayTeam = teamElements[1].innerText.trim();

                        // Marcador: específico de fútbol (.sc-iqGQTr)
                        const scoreElements = Array.from(el.querySelectorAll('.sc-iqGQTr'));
                        if (scoreElements.length < 2) return null;
                        
                        const scoreHome = parseInt(scoreElements[0].innerText) || 0;
                        const scoreAway = parseInt(scoreElements[1].innerText) || 0;

                        // Tiempo: específico de fútbol (.sc-UoxQT)
                        const timeElement = el.querySelector('.sc-UoxQT');
                        let minute = null;
                        if (timeElement) {
                            const timeText = timeElement.innerText.trim();
                            // Usamos regex para capturar los minutos de "28:01", "45:00", etc.
                            const timeMatch = timeText.match(/(\d+):/);
                            if (timeMatch) {
                                minute = parseInt(timeMatch[1]);
                            } else {
                                // Si no hay ":", intentamos sacar el número directamente (ej. "45")
                                minute = parseInt(timeText) || null;
                            }
                        }

                        const card = el.querySelector('[data-testid^="match-card-"]');
                        let matchUrl = null;
                        if (card) {
                            const matchId = card.getAttribute('data-testid').replace('match-card-', '');
                            matchUrl = `https://www.winamax.es/apuestas-deportivas/match/${matchId}`;
                        }

                        return {
                            home_team: homeTeam,
                            away_team: awayTeam,
                            score_home: scoreHome,
                            score_away: scoreAway,
                            minute: minute,
                            match_url: matchUrl
                        };
                    }).filter(m => m !== null);
                }
                """
            )

            return [MatchInfo(**m) for m in matches_data]

        except Exception as e:
            logger.error(f"Error al extraer partidos en vivo: {e}")
            return []

    async def close(self) -> None:
        if self._page:
            await self._page.close()
