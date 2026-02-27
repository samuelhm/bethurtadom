from abc import ABC, abstractmethod

from src.models.odds import ScrapedData


class BaseScraper(ABC):
    """Interfaz obligatoria para todos los scrapers de casas de apuestas.

    Cualquier nueva web de apuestas DEBE heredar de esta clase e implementar
    sus métodos abstractos para garantizar la compatibilidad con el motor.
    """

    @abstractmethod
    async def login(self) -> bool:
        """Realiza el proceso de login en la web de apuestas.

        Returns:
            bool: True si el login fue exitoso, False en caso contrario.
        """
        pass

    @abstractmethod
    async def get_live_matches(self) -> list[ScrapedData]:
        """Navega por la sección 'En Vivo' y extrae las cuotas de 'Próximo Gol'.

        Returns:
            List[ScrapedData]: Lista de objetos Pydantic con la información extraída.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Cierra el navegador y limpia los recursos de Playwright."""
        pass
