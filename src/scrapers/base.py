from abc import ABC, abstractmethod

from src.models.odds import MatchInfo


class BaseScraper(ABC):
    """Interfaz obligatoria para todos los scrapers de casas de apuestas.

    Cualquier nueva web de apuestas DEBE heredar de esta clase e implementar
    sus métodos abstractos para garantizar la compatibilidad con el motor.
    """

    @abstractmethod
    async def start(self) -> bool:
        """Inicializa el scraper y prepara la página inicial.

        Returns:
            bool: True si la inicialización fue exitosa, False en caso contrario.
        """
        pass

    @abstractmethod
    async def login(self) -> bool:
        """Realiza el proceso de login en la web de apuestas si es necesario.

        Returns:
            bool: True si el login fue exitoso, False en caso contrario.
        """
        pass

    @abstractmethod
    async def navigate_to_live(self) -> bool:
        """Navega a la sección de fútbol 'En Vivo' de la casa de apuestas.

        Returns:
            bool: True si la navegación fue exitosa, False en caso contrario.
        """
        pass

    @abstractmethod
    async def get_live_matches(self) -> list[MatchInfo]:
        """Extrae la información de los partidos y sus cuotas.

        Returns:
            list[MatchInfo]: Lista de objetos Pydantic con la información básica.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Cierra el navegador y limpia los recursos del scraper."""
        pass
