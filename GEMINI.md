# GEMINI.md - Reglas del Proyecto 🤖

## Estilo de Comunicación (Perfil Estudiante)
- **Pasos Pequeños:** Las tareas se dividirán en hitos manejables. No se realizarán grandes cambios de una sola vez.
- **Explicación Detallada:** Cada decisión técnica, patrón de diseño o librería utilizada debe ser explicada didácticamente.
- **Propuestas Incrementales:** Sugerir siempre el siguiente paso lógico, manteniendo la visión de la arquitectura final.

## Gestión de la Arquitectura
- **Registro de Decisiones:** Cualquier cambio nuclear o nuevo patrón (ej. Strategy, Factory, etc.) debe documentarse aquí.
- **Limpieza de Datos:** Eliminar información obsoleta de este archivo cuando ya no sea relevante para el desarrollo futuro.

### Decisiones registradas
- **2026-02-28 · Refactor de `main.py` a orquestador:**
	- Se extrajo la lógica de render HTML a `src/ui/dashboard_renderer.py`.
	- Se extrajo la lógica HTTP + endpoint de enlace a `src/ui/dashboard_server.py`.
	- Se extrajo la lógica operativa de scrapers/loops a `src/core/monitoring.py`.
	- `main.py` queda enfocado en composición de dependencias y ciclo de vida (start/stop), reduciendo acoplamiento y tamaño del archivo.
- **2026-02-28 · Configuración centralizada de arranque:**
	- Se creó `src/core/settings.py` para concentrar rutas del proyecto y configuración del dashboard.
	- `main.py` deja de construir paths/config localmente y consume constantes compartidas.
	- Esto facilita mover parámetros a entorno/CLI en un siguiente paso sin tocar la orquestación.

## Estándares de Código
- **Linter:** Ejecutar `ruff check --fix .` y `ruff format .` después de cualquier cambio.
- **Tipado:** Obligatorio el uso de Type Hints en todas las firmas de funciones y métodos.
- **Validación:** No usar diccionarios planos para datos de apuestas; usar siempre modelos de **Pydantic**.
- **Asyncio:** Toda operación de E/S (Playwright, Red, Archivos) debe ser asíncrona.

## Arquitectura Base
- **Scrapers:** Nuevas webs deben heredar de `src.scrapers.base.BaseScraper`.
- **Excepciones:** Capturar errores de Playwright de forma específica para evitar cierres inesperados del programa.
- **Normalización:** Los nombres de equipos deben normalizarse en el scraper antes de pasarlos al motor de detección.
