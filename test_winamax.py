import asyncio
import sys

from dotenv import load_dotenv

from src.core.browser import BrowserManager
from src.scrapers.winamax import WinamaxScraper


async def main() -> None:
    # 0. Cargamos variables de entorno (.env)
    load_dotenv()

    # 1. Creamos el gestor del navegador (Visible para inspección inicial)
    # Una vez que estemos seguros, cambiaremos a headless=True
    browser = BrowserManager(headless=False)

    # 2. Creamos el scraper pasándole el gestor
    scraper = WinamaxScraper(browser)

    try:
        print("🚀 Iniciando el motor de Winamax...")

        # 3. Intentamos el login completo
        if not await scraper.login():
            print("❌ Error crítico: No se pudo completar el login.")
            return

        # 4. Bucle principal de monitorización
        # El programa se quedará "escuchando" cambios hasta que lo pares (Ctrl+C)
        print("\n📺 MONITORIZACIÓN ACTIVA 📺")
        print("Tip: Pulsa Ctrl + C para detener el programa de forma segura.")

        # Mantenemos la sesión abierta en la página en vivo hasta interrupción manual
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("\n🛑 Deteniendo el programa por el usuario...")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    finally:
        # 5. Muy importante: cerramos TODO para no dejar procesos abiertos
        print("🧹 Limpiando y cerrando pestañas...")
        await scraper.close()
        await browser.stop()


if __name__ == "__main__":
    # Ajustamos el límite de recursión para evitar problemas en bucles largos
    sys.setrecursionlimit(2000)
    asyncio.run(main())
