from playwright.async_api import Page
from src.core.logger import logger


async def login_winamax(page: Page, username: str, password: str, birthday: str) -> bool:
    """Realiza el proceso de login en Winamax."""
    try:
        await page.get_by_text("Conectarse").first.click()

        # Trabajar con el iframe de login
        login_frame = page.frame_locator('iframe[name="login"]')
        await login_frame.get_by_role("textbox", name="Email o número de móvil").fill(username)
        await login_frame.get_by_role("textbox", name="Contraseña").fill(password)
        await login_frame.get_by_role("button", name="Conectarse").click()
        day, month, year = birthday.split("/")
        await login_frame.get_by_role("textbox", name="DD").fill(day)
        await login_frame.get_by_role("textbox", name="MM").fill(month)
        await login_frame.get_by_role("textbox", name="AAAA").fill(year)
        await login_frame.get_by_role("button", name="Conectarse").click()
        #todo: revisar si necesario Espera de seguridad para completar la sesión
        await page.wait_for_timeout(4000)
        return True
    except Exception as e:
        logger.error(f"Error durante el proceso de login: {e}")
        return False
