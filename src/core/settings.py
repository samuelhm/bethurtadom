from pathlib import Path

from src.ui.dashboard_server import DashboardServerConfig

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEAM_NAME_MAPPINGS_PATH = PROJECT_ROOT / "src" / "engine" / "team_name_mappings.json"

DASHBOARD_CONFIG = DashboardServerConfig(
    host="127.0.0.1",
    port=8765,
    refresh_seconds=5,
    scrape_interval_seconds=1.0,
    template_path=PROJECT_ROOT / "src" / "ui" / "dashboard_template.html",
    css_path=PROJECT_ROOT / "src" / "ui" / "dashboard.css",
    js_path=PROJECT_ROOT / "src" / "ui" / "dashboard.js",
)
