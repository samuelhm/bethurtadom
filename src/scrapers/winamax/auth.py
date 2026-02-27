from playwright.async_api import Page

from src.core.logger import logger


async def login_winamax(page: Page, username: str, password: str, birthday: str) -> bool:
    """Realiza el proceso de login en Winamax."""
    try:
        logger.debug("auth.py: Clicking 'Conectarse' button to open login panel")
        await page.get_by_text("Conectarse").first.click()

        logger.debug("auth.py: Switching to 'login' iframe and filling credentials")
        login_frame = page.frame_locator('iframe[name="login"]')
        await login_frame.get_by_role("textbox", name="Email o número de móvil").fill(username)
        await login_frame.get_by_role("textbox", name="Contraseña").fill(password)
        await login_frame.get_by_role("button", name="Conectarse").click()

        logger.debug("auth.py: Splitting birthday and filling day/month/year fields")
        day, month, year = birthday.split("/")
        await login_frame.get_by_role("textbox", name="DD").fill(day)
        await login_frame.get_by_role("textbox", name="MM").fill(month)
        await login_frame.get_by_role("textbox", name="AAAA").fill(year)
        await login_frame.get_by_role("button", name="Conectarse").click()

        logger.debug("auth.py: Waiting for 4000ms timeout to ensure session establishment")
        await page.wait_for_timeout(4000)
        return True
    except Exception as e:
        logger.error(f"Error durante el proceso de login: {e}")
        return False
