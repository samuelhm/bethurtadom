import asyncio
import sys

from dotenv import load_dotenv

from src.core.browser import BrowserManager
from src.core.logger import logger, setup_logger
from src.scrapers.winamax import WinamaxScraper

logger.debug(
    "cada hijo del elemento ReactVirtualized__Grid__innerScrollContainer es un partido en directo, con sus datos dentro de sus hijos (equipos, cuotas, etc)"
)


async def main() -> None:
    logger.debug("main: Calling load_dotenv() to read environment variables")
    load_dotenv()

    logger.debug("main: Setting up project logger with 'INFO' level")
    setup_logger("INFO")

    logger.debug("main: Initializing BrowserManager(headless=False)")
    browser = BrowserManager(headless=False)

    logger.debug("main: Initializing WinamaxScraper with the browser manager")
    scraper = WinamaxScraper(browser)

    try:
        logger.info("🚀 Iniciando el motor de Winamax...")
        logger.debug("main: Executing scraper.start() for initial browser setup")
        if not await scraper.start():
            logger.error("No se pudo iniciar el scraper.")
            return

        logger.debug("main: Executing scraper.navigate_to_live() skipping authentication")
        if not await scraper.navigate_to_live():
            logger.error("No se pudo navegar a la sección en vivo.")
            return

        logger.info("📺 MONITORIZACIÓN ACTIVA 📺")
        logger.info("Tip: Pulsa Ctrl + C para detener el programa de forma segura.")
        logger.debug("main: Calling scraper.get_live_matches() to extract current football data")
        matches = await scraper.get_live_matches()

        if not matches:
            logger.warning("No se encontraron partidos de fútbol en vivo en este momento.")
        else:
            logger.info(f"⚽ Se han encontrado {len(matches)} partidos:")
            for m in matches:
                print(
                    f"[{m.minute or '??'}' ] {m.home_team} {m.score_home} - {m.score_away} {m.away_team}"
                )
                if m.match_url:
                    print(f"    🔗 {m.match_url}")
        await scraper.login()
        logger.debug("main: Hanging execution with asyncio.Event().wait() to keep session alive")
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
    finally:
        logger.info("🧹 Limpiando y cerrando pestañas...")
        await scraper.close()
        await browser.stop()


if __name__ == "__main__":
    sys.setrecursionlimit(2000)
    asyncio.run(main())
