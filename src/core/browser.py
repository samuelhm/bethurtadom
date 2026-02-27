from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.core.logger import logger


class BrowserManager:
    def __init__(self, headless: bool = True) -> None:

        self.headless = headless
        self._pw = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        logger.debug("BrowserManager: Starting Playwright and launching browser")
        if not self._pw:
            self._pw = await async_playwright().start()
            self._browser = await self._pw.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )

    async def get_new_page(self) -> Page:
        logger.debug("BrowserManager: Request received for new page")
        if not self._browser:
            await self.start()

        if not self._browser:
            raise RuntimeError("No se pudo iniciar el navegador")

        logger.debug(
            "BrowserManager: Creating new BrowserContext with custom User-Agent and Viewport"
        )
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        context: BrowserContext = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080}, user_agent=user_agent
        )
        return await context.new_page()

    async def stop(self) -> None:
        logger.debug("BrowserManager: Stopping browser and Playwright")
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
