# GEMINI.md - Reglas del Proyecto 🤖

## Estilo de Comunicación (Perfil Estudiante)
- **Pasos Pequeños:** Las tareas se dividirán en hitos manejables. No se realizarán grandes cambios de una sola vez.
- **Explicación Detallada:** Cada decisión técnica, patrón de diseño o librería utilizada debe ser explicada didácticamente.
- **Propuestas Incrementales:** Sugerir siempre el siguiente paso lógico, manteniendo la visión de la arquitectura final.

## Gestión de la Arquitectura
- **Registro de Decisiones:** Cualquier cambio nuclear o nuevo patrón (ej. Strategy, Factory, etc.) debe documentarse aquí.
- **Limpieza de Datos:** Eliminar información obsoleta de este archivo cuando ya no sea relevante para el desarrollo futuro.

## Estándares de Código
- **Linter:** Ejecutar `ruff check --fix .` y `ruff format .` después de cualquier cambio.
- **Tipado:** Obligatorio el uso de Type Hints en todas las firmas de funciones y métodos.
- **Validación:** No usar diccionarios planos para datos de apuestas; usar siempre modelos de **Pydantic**.
- **Asyncio:** Toda operación de E/S (Playwright, Red, Archivos) debe ser asíncrona.

## Arquitectura Base
- **Scrapers:** Nuevas webs deben heredar de `src.scrapers.base.BaseScraper`.
- **Excepciones:** Capturar errores de Playwright de forma específica para evitar cierres inesperados del programa.
- **Normalización:** Los nombres de equipos deben normalizarse en el scraper antes de pasarlos al motor de detección.
