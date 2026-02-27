import os
from typing import List
from dotenv import load_dotenv
from playwright.async_api import Page
from src.core.browser import BrowserManager
from src.models.odds import ScrapedData
from src.scrapers.base import BaseScraper

# Cargamos las variables del archivo .env
load_dotenv()

class WinamaxScraper(BaseScraper):
    """Implementación del scraper para la web de Winamax."""

    def __init__(self, browser_manager: BrowserManager) -> None:
        """Inicializa el scraper de Winamax."""
        self.browser_manager = browser_manager
        self._page: Page | None = None
        self._base_url = "https://www.winamax.es/apuestas-deportivas"
        self._username = os.getenv("WINAMAX_USER")
        self._password = os.getenv("WINAMAX_PASS")
        self._birthday = os.getenv("WINAMAX_BIRTHDAY")

    async def _setup_page(self) -> None:
        """Obtiene una nueva página del gestor de navegación si no existe."""
        if not self._page:
            self._page = await self.browser_manager.get_new_page()

    async def _handle_popups(self) -> None:
        """Busca y cierra el banner de cookies y el modal publicitario."""
        try:
            cookie_selector = "#tarteaucitronPersonalize2"
            await self._page.wait_for_selector(cookie_selector, state="visible", timeout=3000)
            await self._page.click(cookie_selector)
            await self._page.wait_for_timeout(1000)
        except Exception:
            pass

        try:
            close_modal_selector = "[aria-label='Cerrar']"
            await self._page.wait_for_selector(close_modal_selector, state="visible", timeout=3000)
            await self._page.click(close_modal_selector)
            await self._page.wait_for_timeout(500)
        except Exception:
            pass

    async def login(self) -> bool:
        """Realiza el login completo en Winamax manejando el Iframe de login."""
        if not self._username or not self._password or not self._birthday:
            print("❌ Error: Faltan credenciales o fecha en el .env")
            return False

        await self._setup_page()
        if not self._page:
            return False
            
        print(f"🌐 Navegando a {self._base_url}...")
        await self._page.goto(self._base_url, wait_until="networkidle")
        await self._handle_popups()
        
        print("🖱️ Abriendo menú de login...")
        try:
            await self._page.get_by_text("Conectarse").first.click()
            await self._page.wait_for_timeout(2000)
        except Exception as e:
            print(f"❌ Fallo al pulsar Conectarse: {e}")
            return False

        print("🖼️ Accediendo al Iframe de login...")
        try:
            # 1. Localizamos el Iframe
            login_frame = self._page.frame_locator('iframe[name="login"]')
            
            # 2. Paso 1: Usuario y Contraseña
            print("✍️ Introduciendo Email y Contraseña...")
            user_input = login_frame.get_by_role("textbox", name="Email o número de móvil")
            await user_input.wait_for(state="visible", timeout=10000)
            
            await user_input.fill(self._username)
            await login_frame.get_by_role("textbox", name="Contraseña").fill(self._password)
            
            # Pulsamos el primer "Conectarse"
            await login_frame.get_by_role("button", name="Conectarse").click()
            await self._page.wait_for_timeout(2000)
            
            # 3. Paso 2: Fecha de Nacimiento (dentro del mismo Iframe)
            print(f"🎂 Introduciendo fecha de nacimiento: {self._birthday}")
            day, month, year = self._birthday.split("/")
            
            # Usamos los selectores de rol que descubriste
            day_input = login_frame.get_by_role("textbox", name="DD")
            await day_input.wait_for(state="visible", timeout=5000)
            
            await day_input.fill(day)
            await login_frame.get_by_role("textbox", name="MM").fill(month)
            await login_frame.get_by_role("textbox", name="AAAA").fill(year)
            
            # Pulsamos el "Conectarse" final
            print("🚀 Enviando formulario final...")
            await login_frame.get_by_role("button", name="Conectarse").click()
            
            # Esperamos a que el login procese y desaparezca el iframe
            await self._page.wait_for_timeout(5000)
            print("✅ Login procesado.")

            # --- NAVEGACIÓN POST-LOGIN ---
            
            # 1. Navegar a "En directo"
            print("🏟️ Navegando a la sección 'En directo'...")
            try:
                live_link = self._page.get_by_role("link", name="En directo")
                await live_link.wait_for(state="visible", timeout=5000)
                await live_link.click()
            except Exception as e:
                print(f"❌ Error al navegar a 'En directo': {e}")
                await self._page.goto(f"{self._base_url}/live")

            # 2. Cerrar posibles modales tras la navegación (como el que me pasaste)
            try:
                # Buscamos el botón "Cerrar" con un timeout corto
                close_btn = self._page.get_by_role("button", name="Cerrar")
                if await close_btn.is_visible(timeout=3000):
                    print("✖️ Modal post-navegación detectado. Cerrando...")
                    await close_btn.click()
                    await self._page.wait_for_timeout(1000)
            except Exception:
                pass

            # 3. Filtrar por Fútbol
            print("⚽ Filtrando por partidos de Fútbol...")
            try:
                soccer_btn = self._page.get_by_role("button", name="Fútbol")
                await soccer_btn.wait_for(state="visible", timeout=5000)
                await soccer_btn.click()
                print("✅ Filtro de Fútbol aplicado.")
                await self._page.wait_for_timeout(1500)
            except Exception as e:
                print(f"❌ Error al filtrar por Fútbol: {e}")
                return False

            return True
            
        except Exception as e:
            print(f"❌ Error durante el proceso de login: {e}")
            await self._page.screenshot(path="debug_error_login.png")
            return False

    async def get_live_matches(self) -> List[ScrapedData]:
        return []

    async def close(self) -> None:
        if self._page:
            await self._page.close()
