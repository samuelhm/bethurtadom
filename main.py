import asyncio
import sys

from dotenv import load_dotenv

from src.core.logger import logger, setup_logger
from src.core.monitoring import (
    build_initial_dashboard_html,
    command_loop,
    monitor_loop,
    start_bet365_scraper,
    start_winamax_scraper,
)
from src.core.settings import DASHBOARD_CONFIG, TEAM_NAME_MAPPINGS_PATH
from src.engine.team_name_normalizer import load_team_name_mappings
from src.ui.dashboard_server import (
    DashboardState,
    load_dashboard_assets,
    open_dashboard_windows,
    start_dashboard_server,
)


async def main() -> None:
    setup_logger("INFO")
    load_dotenv()
    team_name_mappings = load_team_name_mappings(TEAM_NAME_MAPPINGS_PATH)
    dashboard_state = DashboardState(team_name_mappings, TEAM_NAME_MAPPINGS_PATH)
    dashboard_assets = load_dashboard_assets(DASHBOARD_CONFIG)
    stop_event = asyncio.Event()

    logger.info("🚀 Iniciando monitor persistente Winamax + Bet365...")
    winamax_runtime, bet365_runtime = await asyncio.gather(
        start_winamax_scraper(), start_bet365_scraper()
    )

    if not winamax_runtime or not bet365_runtime:
        logger.error("No se pudo inicializar uno o más scrapers. Abortando monitor.")
        return

    winamax_browser, winamax_scraper = winamax_runtime
    bet365_browser, bet365_scraper = bet365_runtime

    initial_html = build_initial_dashboard_html(
        assets=dashboard_assets,
        config=DASHBOARD_CONFIG,
    )
    await dashboard_state.set_html(initial_html)
    dashboard_server = await start_dashboard_server(
        state=dashboard_state,
        config=DASHBOARD_CONFIG,
        assets=dashboard_assets,
    )
    open_dashboard_windows(DASHBOARD_CONFIG)

    monitor_task = asyncio.create_task(
        monitor_loop(
            winamax_scraper,
            bet365_scraper,
            team_name_mappings,
            dashboard_state,
            dashboard_assets,
            DASHBOARD_CONFIG,
            stop_event,
        )
    )
    command_task = asyncio.create_task(
        command_loop(
            stop_event=stop_event,
            open_dashboard_callback=lambda: open_dashboard_windows(DASHBOARD_CONFIG),
        )
    )

    try:
        await asyncio.gather(monitor_task, command_task)
    except KeyboardInterrupt:
        stop_event.set()
    finally:
        dashboard_server.close()
        await dashboard_server.wait_closed()
        await winamax_scraper.close()
        await bet365_scraper.close()
        await winamax_browser.stop()
        await bet365_browser.stop()


if __name__ == "__main__":
    sys.setrecursionlimit(2000)
    asyncio.run(main())
