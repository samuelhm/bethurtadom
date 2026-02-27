from playwright.async_api import Page


async def go_to_live_football(page: Page, base_url: str) -> bool:
    """Navega a la sección 'En directo' y aplica el filtro de 'Fútbol'."""
    try:
        print("🏟️ Navegando a 'En directo'...")
        await page.goto(f"{base_url}/live", wait_until="load")
        await page.mouse.click(10, 10)

        print("⚽ Filtrando por Fútbol...")
        await page.get_by_role("button", name="Fútbol").first.click()

        # todo: Pequeña espera para que la lista de partidos se actualice revisar si necesario
        await page.wait_for_timeout(3000)
        await page.pause()  # Pausa para inspección manual, eliminar en producción
        return True
    except Exception as e:
        print(f"❌ Error durante la navegación a Fútbol en Vivo: {e}")
        return False
