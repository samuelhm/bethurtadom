import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserManager:
    """
    Gestor central de Playwright para controlar la instancia del navegador.
    
    Esta clase asegura que no abramos múltiples navegadores innecesariamente
    y proporciona una interfaz limpia para obtener nuevas páginas.
    """

    def __init__(self, headless: bool = True):
        """
        Inicializa el gestor.
        Args:
            headless: Si es True, el navegador no será visible.
        """
        self.headless = headless
        self._pw = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        """Inicia la instancia de Playwright y el navegador."""
        if not self._pw:
            self._pw = await async_playwright().start()
            self._browser = await self._pw.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"] # Ayuda a evitar detecciones
            )

    async def get_new_page(self) -> Page:
        """
        Crea un nuevo contexto y una nueva página.
        Returns:
            Page: Una nueva pestaña del navegador lista para usar.
        """
        if not self._browser:
            await self.start()
        
        # Creamos un contexto (como una sesión de incógnito nueva cada vez)
        context: BrowserContext = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        return await context.new_page()

    async def stop(self) -> None:
        """Cierra el navegador y limpia Playwright."""
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
