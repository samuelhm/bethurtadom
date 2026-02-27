import asyncio
from src.core.browser import BrowserManager
from src.scrapers.winamax import WinamaxScraper


async def main() -> None:
    # 1. Creamos el gestor del navegador (headless=False para verlo!)
    browser = BrowserManager(headless=False)
    
    # 2. Creamos el scraper pasándole el gestor
    scraper = WinamaxScraper(browser)
    
    try:
        print("🚀 Iniciando el navegador...")
        success = await scraper.login()
        
        if success:
            print("✅ ¡Conectado con éxito a Winamax!")
            # Esperamos 5 segundos para que puedas verlo en pantalla
            await asyncio.sleep(5)
        else:
            print("❌ Error al conectar.")
            
    finally:
        # 3. Muy importante: cerramos TODO para no dejar procesos abiertos
        print("🧹 Limpiando y cerrando...")
        await scraper.close()
        await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
