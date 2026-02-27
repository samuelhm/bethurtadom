from playwright.async_api import Page
from src.core.logger import logger


async def go_to_live_football(page: Page, base_url: str) -> bool:
    """Navega a la sección 'En directo' y aplica el filtro de 'Fútbol'."""
    try:
        logger.debug(f"navigation.py: Navigating to {base_url}/live with wait_until='load'")
        await page.goto(f"{base_url}/live", wait_until="load")
        
        logger.debug("navigation.py: Clicking at (10, 10) to dismiss any overlays")
        await page.mouse.click(10, 10)

        logger.debug("navigation.py: Filtering live matches by 'Fútbol'")
        await page.get_by_role("button", name="Fútbol").first.click()

        logger.debug("navigation.py: Waiting 3000ms for list to refresh after filter")
        await page.wait_for_timeout(3000)
        return True
    except Exception as e:
        logger.error(f"Error durante la navegación a Fútbol en Vivo: {e}")
        return False
