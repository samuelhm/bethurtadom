import asyncio
import sys

from src.core.browser import BrowserManager
from src.core.logger import logger, setup_logger
from src.scrapers.bet365 import Bet365Scraper


async def main() -> None:
    setup_logger("INFO")
    browser = BrowserManager(headless=False)
    scraper = Bet365Scraper(browser)

    try:
        if not await scraper.start():
            logger.error("No se pudo iniciar Bet365.")
            return

        logger.info("📡 Extrayendo partidos en vivo de Bet365...")
        matches = await scraper.get_live_matches()
        
        if not matches:
            logger.warning("No se encontraron partidos.")
        else:
            print("\n" + "="*50)
            print(f"⚽ {len(matches)} PARTIDOS ENCONTRADOS")
            print("="*50)
            for m in matches:
                time = f"{m.minute}'" if m.minute else "??"
                print(f"[{time:^5}] {m.home_team} {m.score_home} - {m.score_away} {m.away_team}")
                print(f"        🏆 {m.competition}")
            print("="*50 + "\n")

        logger.info("Sesión activa. Pulsa Ctrl+C para salir.")
        await asyncio.Event().wait()

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await scraper.close()
        await browser.stop()


if __name__ == "__main__":
    sys.setrecursionlimit(2000)
    asyncio.run(main())
