# Bethurtadom ⚽️💰

Scanner inteligente de discrepancias en cuotas de apuestas deportivas en vivo (Live Betting) enfocado en el mercado de "Próximo Gol".

## 🏗️ Arquitectura del Sistema

El proyecto sigue una arquitectura modular y escalable, utilizando patrones de diseño para facilitar la adición de nuevas casas de apuestas sin modificar el núcleo del motor.

### Componentes Principales

1.  **`src.models` (Pydantic Layer):**
    *   Uso de **Pydantic v2** para definir esquemas estrictos de datos (`Match`, `Odds`, `Market`).
    *   Garantiza que las cuotas sean siempre flotantes y que los nombres de los equipos estén normalizados.

2.  **`src.scrapers` (Strategy Pattern):**
    *   `BaseScraper` (Clase Abstracta): Define el contrato obligatorio (`login()`, `get_live_matches()`, `close()`).
    *   Implementaciones Concretas: `Bet365Scraper`, `WinamaxScraper`. Cada una encapsula la lógica de navegación específica de la web.

3.  **`src.engine` (Detector Layer):**
    *   Motor de detección que compara datos recolectados por los scrapers.
    *   Identifica discrepancias significativas basándose en umbrales configurables.

4.  **`src.core.browser`:**
    *   Gestor central de instancias de **Playwright** para optimizar el uso de recursos y manejar el contexto del navegador.

## 🛠️ Stack Tecnológico

*   **Lenguaje:** Python 3.14 (Asyncio)
*   **Automatización:** [Playwright](https://playwright.dev/python/) (Soporte nativo para SPAs y bypass de bots básicos).
*   **Validación:** [Pydantic](https://docs.pydantic.dev/) (Modelos de datos con tipos estrictos).
*   **Linter/Formatter:** [Ruff](https://astral.sh/ruff) (Configuración ultra-estricta para código limpio).
*   **Logging:** `structlog` (Logs estructurados para facilitar el debugging en ejecución paralela).

## 🚀 Instalación y Uso

```bash
# Instalar dependencias
pip install -e .

# Instalar navegadores de Playwright
playwright install chromium
```

## 📏 Normas de Desarrollo

1.  **Tipado Estricto:** Todas las funciones deben incluir type-hints.
2.  **Async-first:** Todo el scraping y procesamiento debe ser asíncrono.
3.  **Tests:** Cada scraper debe tener su suite de tests simulando el DOM de la web.
