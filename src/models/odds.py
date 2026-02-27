from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class BookmakerName(StrEnum):
    """Enumeración de casas de apuestas soportadas."""

    BET365 = "bet365"
    WINAMAX = "winamax"


class NextGoalMarket(BaseModel):
    """Modelo para el mercado de Próximo Gol."""

    home_odds: Annotated[float, Field(gt=1.0)]
    away_odds: Annotated[float, Field(gt=1.0)]
    no_goal_odds: Annotated[float, Field(gt=1.0)]
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("home_odds", "away_odds", "no_goal_odds", mode="before")
    @classmethod
    def validate_odds(cls, v: float | str) -> float:
        """Convierte cuotas de string a float si es necesario y las valida."""
        if isinstance(v, str):
            v = float(v.replace(",", "."))
        return v


class MatchInfo(BaseModel):
    """Información básica de un partido en vivo."""

    home_team: str
    away_team: str
    match_url: str | None = None
    score_home: int = 0
    score_away: int = 0
    minute: int | None = None
    competition: str | None = None


class ScrapedData(BaseModel):
    """Datos consolidados de un partido para una casa específica."""

    bookmaker: BookmakerName
    match: MatchInfo
    market: NextGoalMarket
