import html
import json
from collections import defaultdict

from src.models.odds import MatchInfo


def format_minute(minute: int | None) -> str:
    """Formatea el minuto de juego para dashboard."""
    return f"{minute}'" if minute is not None else "??"


def truncate_text(text: str, max_length: int) -> str:
    """Trunca texto largo respetando longitud máxima."""
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 1]}…"


def format_match_line(match: MatchInfo, max_length: int) -> str:
    """Construye una línea compacta para una celda de partido."""
    base_text = f"{match.home_team} {match.score_home}-{match.score_away} {match.away_team}"
    return truncate_text(base_text, max_length)


def build_rows_by_minute(
    winamax_matches: list[MatchInfo],
    bet365_matches: list[MatchInfo],
    empty_message: str = "No se encontraron partidos en vivo.",
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
        return [("--", empty_message, empty_message)]

    rows: list[tuple[str, str, str]] = []
    for minute in all_minutes:
        winamax_rows = winamax_by_minute.get(minute, [])
        bet365_rows = bet365_by_minute.get(minute, [])
        total_rows = max(len(winamax_rows), len(bet365_rows), 1)

        for row_index in range(total_rows):
            minute_text = format_minute(minute) if row_index == 0 else ""
            winamax_text = ""
            bet365_text = ""

            if row_index < len(winamax_rows):
                winamax_text = format_match_line(winamax_rows[row_index], 200)
            if row_index < len(bet365_rows):
                bet365_text = format_match_line(bet365_rows[row_index], 200)

            rows.append((minute_text, winamax_text, bet365_text))

    return rows


def build_rows_by_linked_pairs(
    linked_pairs: list[tuple[MatchInfo, MatchInfo]],
    empty_message: str = "No hay partidos enlazados todavía.",
) -> list[tuple[str, str, str]]:
    """Construye filas de partidos enlazados manteniendo cada pareja en la misma fila."""
    if not linked_pairs:
        return [("--", empty_message, empty_message)]

    sorted_pairs = sorted(
        linked_pairs,
        key=lambda pair: (
            pair[0].minute is None and pair[1].minute is None,
            -(
                pair[0].minute
                if pair[0].minute is not None
                else (pair[1].minute if pair[1].minute is not None else -1)
            ),
        ),
    )

    rows: list[tuple[str, str, str]] = []
    for winamax_match, bet365_match in sorted_pairs:
        reference_minute = (
            winamax_match.minute if winamax_match.minute is not None else bet365_match.minute
        )
        rows.append(
            (
                format_minute(reference_minute),
                format_match_line(winamax_match, 200),
                format_match_line(bet365_match, 200),
            )
        )

    return rows


def _build_option_label(match: MatchInfo) -> str:
    minute_text = format_minute(match.minute)
    return (
        f"{minute_text} · {match.home_team} {match.score_home}-{match.score_away} {match.away_team}"
    )


def _build_match_options(matches: list[MatchInfo]) -> str:
    return "\n".join(
        f"<option value='{index}'>{html.escape(_build_option_label(match))}</option>"
        for index, match in enumerate(matches)
    )


def _serialize_matches(matches: list[MatchInfo]) -> str:
    serializable = [
        {
            "home_team": match.home_team,
            "away_team": match.away_team,
        }
        for match in matches
    ]
    serialized = json.dumps(serializable, ensure_ascii=False)
    return serialized.replace("</", "<\\/")


def _render_table_rows(rows: list[tuple[str, str, str]]) -> str:
    return "\n".join(
        (
            "<tr>"
            f"<td>{html.escape(winamax)}</td>"
            f"<td class='minute'>{html.escape(minute)}</td>"
            f"<td>{html.escape(bet365)}</td>"
            "</tr>"
        )
        for minute, winamax, bet365 in rows
    )


def render_dashboard_html(
    dashboard_template: str,
    refresh_seconds: int,
    linked_rows: list[tuple[str, str, str]],
    pending_rows: list[tuple[str, str, str]],
    winamax_total: int,
    bet365_total: int,
    linked_total: int,
    pending_total: int,
    last_update: str,
    winamax_pending_raw_matches: list[MatchInfo],
    bet365_pending_matches: list[MatchInfo],
) -> str:
    """Renderiza el dashboard HTML con tabla comparativa y formulario de enlace."""
    return dashboard_template.format(
        refresh_seconds=refresh_seconds,
        last_update=html.escape(last_update),
        winamax_total=winamax_total,
        bet365_total=bet365_total,
        linked_total=linked_total,
        pending_total=pending_total,
        linked_table_rows=_render_table_rows(linked_rows),
        pending_table_rows=_render_table_rows(pending_rows),
        winamax_options=_build_match_options(winamax_pending_raw_matches),
        bet365_options=_build_match_options(bet365_pending_matches),
        winamax_matches_json=_serialize_matches(winamax_pending_raw_matches),
        bet365_matches_json=_serialize_matches(bet365_pending_matches),
    ).strip()
