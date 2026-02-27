from pydantic import BaseModel


class MatchInfo(BaseModel):
    """Información básica de un partido en vivo."""

    home_team: str
    away_team: str
    match_url: str | None = None
    score_home: int = 0
    score_away: int = 0
    minute: int | None = None
    competition: str | None = None
