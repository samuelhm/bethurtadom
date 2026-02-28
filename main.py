import asyncio
import sys
from collections import defaultdict
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


def assign_match_ids(matches: list[MatchInfo]) -> list[MatchInfo]:
    """Asigna IDs consecutivos desde 0 a la lista de partidos."""
    for match_id, match in enumerate(matches):
        match.id = match_id
    return matches


def _format_minute(minute: int | None) -> str:
    return f"{minute}'" if minute is not None else "??"


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 1]}…"


def _format_match_line(match: MatchInfo, max_length: int) -> str:
    match_id = match.id if match.id is not None else -1
    base_text = (
        f"ID={match_id:<3} "
        f"{match.home_team} {match.score_home}-{match.score_away} {match.away_team}"
    )
    return _truncate(base_text, max_length)


def print_side_by_side_matches(
    winamax_matches: list[MatchInfo], bet365_matches: list[MatchInfo]
) -> None:
    """Muestra tabla comparativa Winamax vs Bet365 agrupada por minuto."""
    winamax_by_minute: dict[int | None, list[MatchInfo]] = defaultdict(list)
    bet365_by_minute: dict[int | None, list[MatchInfo]] = defaultdict(list)

    for match in sorted(
        winamax_matches,
        key=lambda item: (item.minute is None, item.minute if item.minute is not None else 999),
    ):
        winamax_by_minute[match.minute].append(match)

    for match in sorted(
        bet365_matches,
        key=lambda item: (item.minute is None, item.minute if item.minute is not None else 999),
    ):
        bet365_by_minute[match.minute].append(match)

    all_minutes = sorted(
        set(winamax_by_minute.keys()) | set(bet365_by_minute.keys()),
        key=lambda minute: (minute is None, minute if minute is not None else 999),
    )

    minute_col_width = 6
    site_col_width = 58

    horizontal_line = (
        f"+{'-' * (minute_col_width + 2)}"
        f"+{'-' * (site_col_width + 2)}"
        f"+{'-' * (site_col_width + 2)}+"
    )

    print(f"\n{'=' * 130}")
    print("PARTIDOS EN VIVO (ordenados por minuto)")
    print(f"{'=' * 130}")
    print(horizontal_line)
    print(
        f"| {'MIN':<{minute_col_width}} "
        f"| {'WINAMAX':<{site_col_width}} "
        f"| {'BET365':<{site_col_width}} |"
    )
    print(horizontal_line)

    if not all_minutes:
        empty_text = "No se encontraron partidos en vivo."
        print(
            f"| {'--':<{minute_col_width}} "
            f"| {empty_text:<{site_col_width}} "
            f"| {empty_text:<{site_col_width}} |"
        )
        print(horizontal_line)
        return

    for minute in all_minutes:
        winamax_rows = winamax_by_minute.get(minute, [])
        bet365_rows = bet365_by_minute.get(minute, [])
        total_rows = max(len(winamax_rows), len(bet365_rows), 1)

        for row_index in range(total_rows):
            minute_text = _format_minute(minute) if row_index == 0 else ""

            winamax_text = ""
            if row_index < len(winamax_rows):
                winamax_text = _format_match_line(winamax_rows[row_index], site_col_width)

            bet365_text = ""
            if row_index < len(bet365_rows):
                bet365_text = _format_match_line(bet365_rows[row_index], site_col_width)

            print(
                f"| {minute_text:<{minute_col_width}} "
                f"| {winamax_text:<{site_col_width}} "
                f"| {bet365_text:<{site_col_width}} |"
            )

        print(horizontal_line)


async def run_winamax() -> list[MatchInfo]:
    """Ejecuta el flujo de Winamax y devuelve los partidos en vivo."""
    browser = BrowserManager(headless=False)
    scraper = WinamaxScraper(browser)
    try:
        if not await scraper.start():
            logger.error("Winamax: no se pudo iniciar el scraper.")
            return []
        if not await scraper.navigate_to_live():
            logger.error("Winamax: no se pudo navegar a fútbol en vivo.")
            return []
        return await scraper.get_live_matches()
    except Exception as error:
        logger.error(f"Winamax: error inesperado: {error}")
        return []
    finally:
        await scraper.close()
        await browser.stop()


async def run_bet365() -> list[MatchInfo]:
    """Ejecuta el flujo de Bet365 y devuelve los partidos en vivo."""
    browser = BrowserManager(headless=False)
    scraper = Bet365Scraper(browser)
    try:
        if not await scraper.start():
            logger.error("Bet365: no se pudo iniciar el scraper.")
            return []
        return await scraper.get_live_matches()
    except Exception as error:
        logger.error(f"Bet365: error inesperado: {error}")
        return []
    finally:
        await scraper.close()
        await browser.stop()


async def main() -> None:
    setup_logger("INFO")
    load_dotenv()
    team_name_mappings = load_team_name_mappings(TEAM_NAME_MAPPINGS_PATH)

    logger.info("🚀 Iniciando scrapers de Winamax y Bet365 en paralelo...")
    winamax_matches, bet365_matches = await asyncio.gather(run_winamax(), run_bet365())

    winamax_matches = normalize_matches_team_names("winamax", winamax_matches, team_name_mappings)

    winamax_matches = assign_match_ids(winamax_matches)
    bet365_matches = assign_match_ids(bet365_matches)

    print_side_by_side_matches(winamax_matches, bet365_matches)


if __name__ == "__main__":
    sys.setrecursionlimit(2000)
    asyncio.run(main())
