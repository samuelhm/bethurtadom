import asyncio
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime

from src.core.browser import BrowserManager
from src.core.logger import logger
from src.engine.team_name_normalizer import normalize_matches_team_names
from src.models.odds import MatchInfo
from src.scrapers.bet365 import Bet365Scraper
from src.scrapers.winamax import WinamaxScraper
from src.ui.dashboard_renderer import (
    build_rows_by_linked_pairs,
    build_rows_by_minute,
    render_dashboard_html,
)
from src.ui.dashboard_server import DashboardAssets, DashboardServerConfig, DashboardState


def _build_match_key(home_team: str, away_team: str) -> tuple[str, str]:
    return (home_team.strip().lower(), away_team.strip().lower())


def _split_linked_and_pending_matches(
    winamax_raw_matches: list[MatchInfo],
    winamax_normalized_matches: list[MatchInfo],
    bet365_matches: list[MatchInfo],
) -> tuple[
    list[tuple[MatchInfo, MatchInfo]],
    list[MatchInfo],
    list[MatchInfo],
    list[MatchInfo],
    list[MatchInfo],
    list[MatchInfo],
]:
    """Separa partidos enlazados por nombres normalizados y pendientes de enlazar."""
    bet365_by_key: dict[tuple[str, str], deque[int]] = defaultdict(deque)
    for bet365_index, bet365_match in enumerate(bet365_matches):
        bet365_by_key[_build_match_key(bet365_match.home_team, bet365_match.away_team)].append(
            bet365_index
        )

    linked_pairs: list[tuple[MatchInfo, MatchInfo]] = []
    linked_winamax: list[MatchInfo] = []
    linked_bet365: list[MatchInfo] = []
    pending_winamax_raw: list[MatchInfo] = []
    pending_winamax_normalized: list[MatchInfo] = []
    used_bet365_indexes: set[int] = set()

    for index, normalized_match in enumerate(winamax_normalized_matches):
        key = _build_match_key(normalized_match.home_team, normalized_match.away_team)
        available_indexes = bet365_by_key.get(key)

        if available_indexes:
            bet365_index = available_indexes.popleft()
            linked_winamax.append(normalized_match)
            linked_bet365.append(bet365_matches[bet365_index])
            linked_pairs.append((normalized_match, bet365_matches[bet365_index]))
            used_bet365_indexes.add(bet365_index)
            continue

        pending_winamax_raw.append(winamax_raw_matches[index])
        pending_winamax_normalized.append(normalized_match)

    pending_bet365 = [
        bet365_match
        for bet365_index, bet365_match in enumerate(bet365_matches)
        if bet365_index not in used_bet365_indexes
    ]

    return (
        linked_pairs,
        linked_winamax,
        linked_bet365,
        pending_winamax_raw,
        pending_winamax_normalized,
        pending_bet365,
    )


async def start_winamax_scraper() -> tuple[BrowserManager, WinamaxScraper] | None:
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


async def start_bet365_scraper() -> tuple[BrowserManager, Bet365Scraper] | None:
    """Inicia Bet365 una sola vez para monitoreo continuo."""
    browser = BrowserManager(headless=False)
    scraper = Bet365Scraper(browser)
    if not await scraper.start():
        logger.error("Bet365: no se pudo iniciar el scraper.")
        await scraper.close()
        await browser.stop()
        return None
    return browser, scraper


def build_initial_dashboard_html(
    assets: DashboardAssets,
    config: DashboardServerConfig,
) -> str:
    """Construye HTML inicial mientras los scrapers cargan datos reales."""
    return render_dashboard_html(
        dashboard_template=assets.template,
        refresh_seconds=config.refresh_seconds,
        linked_rows=[
            ("--", "No hay partidos enlazados todavía.", "No hay partidos enlazados todavía.")
        ],
        pending_rows=[("--", "Cargando Winamax...", "Cargando Bet365...")],
        winamax_total=0,
        bet365_total=0,
        linked_total=0,
        pending_total=0,
        last_update="iniciando",
        winamax_pending_raw_matches=[],
        bet365_pending_matches=[],
    )


async def monitor_loop(
    winamax_scraper: WinamaxScraper,
    bet365_scraper: Bet365Scraper,
    team_name_mappings: dict[str, dict[str, str]],
    dashboard_state: DashboardState,
    dashboard_assets: DashboardAssets,
    dashboard_config: DashboardServerConfig,
    stop_event: asyncio.Event,
) -> None:
    """Mantiene actualizado el dashboard en tiempo real."""
    while not stop_event.is_set():
        winamax_raw_matches, bet365_matches = await asyncio.gather(
            winamax_scraper.get_live_matches(),
            bet365_scraper.get_live_matches(),
        )

        winamax_matches = normalize_matches_team_names(
            "winamax",
            [match.model_copy(deep=True) for match in winamax_raw_matches],
            team_name_mappings,
        )

        (
            linked_pairs,
            linked_winamax,
            linked_bet365,
            pending_winamax_raw,
            pending_winamax_normalized,
            pending_bet365,
        ) = _split_linked_and_pending_matches(
            winamax_raw_matches,
            winamax_matches,
            bet365_matches,
        )

        linked_rows = build_rows_by_linked_pairs(
            linked_pairs,
            empty_message="No hay partidos enlazados todavía.",
        )
        pending_rows = build_rows_by_minute(
            pending_winamax_normalized,
            pending_bet365,
            empty_message="No hay partidos pendientes por enlazar.",
        )
        html_content = render_dashboard_html(
            dashboard_template=dashboard_assets.template,
            refresh_seconds=dashboard_config.refresh_seconds,
            linked_rows=linked_rows,
            pending_rows=pending_rows,
            winamax_total=len(winamax_matches),
            bet365_total=len(bet365_matches),
            linked_total=len(linked_winamax),
            pending_total=max(len(pending_winamax_normalized), len(pending_bet365)),
            last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            winamax_pending_raw_matches=pending_winamax_raw,
            bet365_pending_matches=pending_bet365,
        )
        await dashboard_state.set_html(html_content)

        logger.info(
            f"Dashboard actualizado | Winamax={len(winamax_matches)} | Bet365={len(bet365_matches)}"
        )

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=dashboard_config.scrape_interval_seconds,
            )
        except TimeoutError:
            continue


async def command_loop(
    stop_event: asyncio.Event,
    open_dashboard_callback: Callable[[], None],
) -> None:
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
            open_dashboard_callback()
            print("Ventana del dashboard abierta.")
            continue
        if command:
            print("Comando no reconocido. Usa 'help'.")
