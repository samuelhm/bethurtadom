import asyncio
import html
import sys
import webbrowser
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.core.browser import BrowserManager
from src.core.logger import logger, setup_logger
from src.engine.team_name_normalizer import (
    load_team_name_mappings,
    normalize_matches_team_names,
)
from src.models.odds import MatchInfo
from src.scrapers.bet365 import Bet365Scraper
from src.scrapers.winamax import WinamaxScraper

TEAM_NAME_MAPPINGS_PATH = (
    Path(__file__).resolve().parent / "src" / "engine" / "team_name_mappings.json"
)
DASHBOARD_PATH = Path(__file__).resolve().parent / "live_matches_dashboard.html"
DASHBOARD_TEMPLATE_PATH = Path(__file__).resolve().parent / "src" / "ui" / "dashboard_template.html"
REFRESH_SECONDS = 5

DASHBOARD_TEMPLATE = DASHBOARD_TEMPLATE_PATH.read_text("utf-8")


def _format_minute(minute: int | None) -> str:
    return f"{minute}'" if minute is not None else "??"


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 1]}…"


def _format_match_line(match: MatchInfo, max_length: int) -> str:
    base_text = f"{match.home_team} {match.score_home}-{match.score_away} {match.away_team}"
    return _truncate(base_text, max_length)


def _build_rows_by_minute(
    winamax_matches: list[MatchInfo], bet365_matches: list[MatchInfo]
) -> list[tuple[str, str, str]]:
    """Construye filas de tabla comparativa agrupadas por minuto."""
    winamax_by_minute: dict[int | None, list[MatchInfo]] = defaultdict(list)
    bet365_by_minute: dict[int | None, list[MatchInfo]] = defaultdict(list)

    for match in sorted(
        winamax_matches,
        key=lambda item: (
            item.minute is None,
            -(item.minute if item.minute is not None else -1),
        ),
    ):
        winamax_by_minute[match.minute].append(match)

    for match in sorted(
        bet365_matches,
        key=lambda item: (
            item.minute is None,
            -(item.minute if item.minute is not None else -1),
        ),
    ):
        bet365_by_minute[match.minute].append(match)

    all_minutes = sorted(
        set(winamax_by_minute.keys()) | set(bet365_by_minute.keys()),
        key=lambda minute: (minute is None, -(minute if minute is not None else -1)),
    )

    if not all_minutes:
        return [
            ("--", "No se encontraron partidos en vivo.", "No se encontraron partidos en vivo.")
        ]

    rows: list[tuple[str, str, str]] = []
    for minute in all_minutes:
        winamax_rows = winamax_by_minute.get(minute, [])
        bet365_rows = bet365_by_minute.get(minute, [])
        total_rows = max(len(winamax_rows), len(bet365_rows), 1)

        for row_index in range(total_rows):
            minute_text = _format_minute(minute) if row_index == 0 else ""
            winamax_text = ""
            bet365_text = ""

            if row_index < len(winamax_rows):
                winamax_text = _format_match_line(winamax_rows[row_index], 200)
            if row_index < len(bet365_rows):
                bet365_text = _format_match_line(bet365_rows[row_index], 200)

            rows.append((minute_text, winamax_text, bet365_text))

    return rows


def _render_dashboard_html(
    rows: list[tuple[str, str, str]], winamax_total: int, bet365_total: int, last_update: str
) -> str:
    """Renderiza el dashboard HTML con la tabla comparativa."""
    table_rows = "\n".join(
        (
            "<tr>"
            f"<td>{html.escape(winamax)}</td>"
            f"<td class='minute'>{html.escape(minute)}</td>"
            f"<td>{html.escape(bet365)}</td>"
            "</tr>"
        )
        for minute, winamax, bet365 in rows
    )

    return DASHBOARD_TEMPLATE.format(
        last_update=html.escape(last_update),
        winamax_total=winamax_total,
        bet365_total=bet365_total,
        table_rows=table_rows,
    ).strip()


async def _write_dashboard(html_content: str) -> None:
    """Escribe el HTML del dashboard de forma asíncrona."""
    await asyncio.to_thread(DASHBOARD_PATH.write_text, html_content, "utf-8")


def _open_dashboard_window() -> None:
    """Abre una nueva ventana con el dashboard local."""
    webbrowser.open_new(DASHBOARD_PATH.as_uri())


async def _start_winamax_scraper() -> tuple[BrowserManager, WinamaxScraper] | None:
    """Inicia Winamax una sola vez para monitoreo continuo."""
    browser = BrowserManager(headless=False)
    scraper = WinamaxScraper(browser)
    if not await scraper.start():
        logger.error("Winamax: no se pudo iniciar el scraper.")
        await scraper.close()
        await browser.stop()
        return None
    if not await scraper.navigate_to_live():
        logger.error("Winamax: no se pudo navegar a fútbol en vivo.")
        await scraper.close()
        await browser.stop()
        return None
    return browser, scraper


async def _start_bet365_scraper() -> tuple[BrowserManager, Bet365Scraper] | None:
    """Inicia Bet365 una sola vez para monitoreo continuo."""
    browser = BrowserManager(headless=False)
    scraper = Bet365Scraper(browser)
    if not await scraper.start():
        logger.error("Bet365: no se pudo iniciar el scraper.")
        await scraper.close()
        await browser.stop()
        return None
    return browser, scraper


async def _monitor_loop(
    winamax_scraper: WinamaxScraper,
    bet365_scraper: Bet365Scraper,
    team_name_mappings: dict[str, dict[str, str]],
    stop_event: asyncio.Event,
) -> None:
    """Mantiene actualizado el dashboard en tiempo real."""
    while not stop_event.is_set():
        winamax_matches, bet365_matches = await asyncio.gather(
            winamax_scraper.get_live_matches(), bet365_scraper.get_live_matches()
        )

        winamax_matches = normalize_matches_team_names(
            "winamax", winamax_matches, team_name_mappings
        )

        rows = _build_rows_by_minute(winamax_matches, bet365_matches)
        html_content = _render_dashboard_html(
            rows=rows,
            winamax_total=len(winamax_matches),
            bet365_total=len(bet365_matches),
            last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        await _write_dashboard(html_content)

        logger.info(
            f"Dashboard actualizado | Winamax={len(winamax_matches)} | Bet365={len(bet365_matches)}"
        )

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=REFRESH_SECONDS)
        except TimeoutError:
            continue


async def _command_loop(stop_event: asyncio.Event) -> None:
    """Mantiene la consola principal para comandos de control."""
    help_text = (
        "Comandos disponibles: help | status | open | exit\n"
        "- help: muestra esta ayuda\n"
        "- status: confirma que el monitor sigue activo\n"
        "- open: abre otra ventana del dashboard\n"
        "- exit: detiene el monitor y cierra"
    )
    print(help_text)

    while not stop_event.is_set():
        command = (await asyncio.to_thread(input, "bethurtadom> ")).strip().lower()
        if command in {"exit", "quit", "q"}:
            stop_event.set()
            print("Cerrando monitor...")
            return
        if command == "help":
            print(help_text)
            continue
        if command == "status":
            print("Monitor activo. Dashboard actualizándose en tiempo real.")
            continue
        if command == "open":
            _open_dashboard_window()
            print("Ventana del dashboard abierta.")
            continue
        if command:
            print("Comando no reconocido. Usa 'help'.")


async def main() -> None:
    setup_logger("INFO")
    load_dotenv()
    team_name_mappings = load_team_name_mappings(TEAM_NAME_MAPPINGS_PATH)
    stop_event = asyncio.Event()

    logger.info("🚀 Iniciando monitor persistente Winamax + Bet365...")
    winamax_runtime, bet365_runtime = await asyncio.gather(
        _start_winamax_scraper(), _start_bet365_scraper()
    )

    if not winamax_runtime or not bet365_runtime:
        logger.error("No se pudo inicializar uno o más scrapers. Abortando monitor.")
        return

    winamax_browser, winamax_scraper = winamax_runtime
    bet365_browser, bet365_scraper = bet365_runtime

    initial_html = _render_dashboard_html(
        rows=[("--", "Cargando Winamax...", "Cargando Bet365...")],
        winamax_total=0,
        bet365_total=0,
        last_update="iniciando",
    )
    await _write_dashboard(initial_html)
    _open_dashboard_window()

    monitor_task = asyncio.create_task(
        _monitor_loop(winamax_scraper, bet365_scraper, team_name_mappings, stop_event)
    )
    command_task = asyncio.create_task(_command_loop(stop_event))

    try:
        await asyncio.gather(monitor_task, command_task)
    except KeyboardInterrupt:
        stop_event.set()
    finally:
        await winamax_scraper.close()
        await bet365_scraper.close()
        await winamax_browser.stop()
        await bet365_browser.stop()


if __name__ == "__main__":
    sys.setrecursionlimit(2000)
    asyncio.run(main())
