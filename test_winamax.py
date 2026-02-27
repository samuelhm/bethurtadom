import asyncio
import sys

from dotenv import load_dotenv

from src.core.browser import BrowserManager
from src.core.logger import logger, setup_logger
from src.scrapers.winamax import WinamaxScraper

#cada hijo del elemento ReactVirtualized__Grid__innerScrollContainer es un partido en directo, con sus datos dentro de sus hijos (equipos, cuotas, etc)

async def main() -> None:
    load_dotenv()
    setup_logger("INFO")
    browser = BrowserManager(headless=False)
    scraper = WinamaxScraper(browser)

    try:
        logger.info("🚀 Iniciando el motor de Winamax...")

        # 1. Iniciamos el navegador y navegamos a la web base
        if not await scraper.start():
            logger.error("No se pudo iniciar el scraper.")
            return

        # 2. Navegamos directamente a 'En Vivo' sin loguearnos
        # Si quisieras loguearte, llamarías a await scraper.login() en su lugar
        if not await scraper.navigate_to_live():
            logger.error("No se pudo navegar a la sección en vivo.")
            return

        logger.info("📺 MONITORIZACIÓN ACTIVA 📺")

        logger.info("Tip: Pulsa Ctrl + C para detener el programa de forma segura.")

        # 4. Obtenemos y mostramos los partidos en vivo
        matches = await scraper.get_live_matches()
        
        if not matches:
            logger.warning("No se encontraron partidos de fútbol en vivo en este momento.")
        else:
            logger.info(f"⚽ Se han encontrado {len(matches)} partidos:")
            for m in matches:
                print(f"[{m.minute or '??'}' ] {m.home_team} {m.score_home} - {m.score_away} {m.away_team}")
                if m.match_url:
                    print(f"    🔗 {m.match_url}")

        # Mantenemos la sesión abierta por si el usuario quiere inspeccionar
        if scraper._page:
            # await scraper._page.pause() # Descomentar para inspeccionar manualmente
            pass
            
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
