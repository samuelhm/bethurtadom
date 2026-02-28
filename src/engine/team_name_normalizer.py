import json
from pathlib import Path

from src.core.logger import logger
from src.models.odds import MatchInfo


def load_team_name_mappings(mapping_file: Path) -> dict[str, dict[str, str]]:
    """Carga el JSON de mapeos de nombres por sitio."""
    if not mapping_file.exists():
        logger.warning(f"No existe archivo de mapeo: {mapping_file}")
        return {}

    with mapping_file.open(encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        logger.warning("El archivo de mapeo no tiene formato objeto JSON.")
        return {}

    valid_data: dict[str, dict[str, str]] = {}
    for site_name, site_mapping in data.items():
        if isinstance(site_name, str) and isinstance(site_mapping, dict):
            valid_data[site_name.lower()] = {
                str(source_name): str(target_name)
                for source_name, target_name in site_mapping.items()
            }
    return valid_data


def normalize_matches_team_names(
    site: str,
    matches: list[MatchInfo],
    mappings: dict[str, dict[str, str]],
) -> list[MatchInfo]:
    """Normaliza nombres de equipos para un sitio usando Bet365 como canónico."""
    site_mapping = mappings.get(site.lower(), {})
    if not site_mapping:
        return matches

    for match in matches:
        match.home_team = site_mapping.get(match.home_team, match.home_team)
        match.away_team = site_mapping.get(match.away_team, match.away_team)
    return matches
