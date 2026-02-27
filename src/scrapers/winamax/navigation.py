from playwright.async_api import Page


async def go_to_live_football(page: Page, base_url: str, inspect_mode: bool = False) -> bool:
    """Navega a la sección 'En directo' y aplica el filtro de 'Fútbol'."""
    try:
        print("🏟️ Navegando a 'En directo'...")
        # Usamos 'load' para esperar a que el HTML, CSS y JS básico estén listos
        await page.goto(f"{base_url}/live", wait_until="load")

        # Clic de cortesía para cerrar posibles overlays residuales
        await page.mouse.click(10, 10)

        if inspect_mode:
            print("🧪 Modo inspección activo: Playwright Inspector en pausa.")
            await page.pause()

        print("⚽ Filtrando por Fútbol...")
        # Clic directo en el botón de fútbol
        await page.get_by_role("button", name="Fútbol").first.click()

        # Pequeña espera para que la lista de partidos se actualice
        await page.wait_for_timeout(2000)
        return True
    except Exception as e:
        print(f"❌ Error durante la navegación a Fútbol en Vivo: {e}")
        return False
