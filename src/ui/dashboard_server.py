import asyncio
import json
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ValidationError

from src.core.logger import logger
from src.engine.team_name_normalizer import save_team_name_mappings, upsert_match_team_mapping


class LinkMatchPayload(BaseModel):
    """Payload mínimo de un partido usado para enlazar nombres de equipos."""

    home_team: str
    away_team: str


class LinkRequestPayload(BaseModel):
    """Payload del endpoint que enlaza un partido Winamax con uno Bet365."""

    winamax_match: LinkMatchPayload
    bet365_match: LinkMatchPayload


@dataclass(frozen=True)
class DashboardServerConfig:
    """Configuración del servidor HTTP del dashboard."""

    host: str
    port: int
    refresh_seconds: int
    scrape_interval_seconds: float
    template_path: Path
    css_path: Path
    js_path: Path


@dataclass(frozen=True)
class DashboardAssets:
    """Activos estáticos usados por el dashboard."""

    template: str
    css: str
    js: str


class DashboardState:
    """Estado compartido entre monitor y servidor HTTP local."""

    def __init__(
        self,
        team_name_mappings: dict[str, dict[str, str]],
        mappings_path: Path,
    ) -> None:
        self._html = ""
        self._lock = asyncio.Lock()
        self._team_name_mappings = team_name_mappings
        self._mappings_path = mappings_path

    async def set_html(self, html_content: str) -> None:
        """Actualiza el HTML servido por el dashboard."""
        async with self._lock:
            self._html = html_content

    async def get_html(self) -> str:
        """Obtiene el HTML actual del dashboard."""
        async with self._lock:
            return self._html

    async def link_matches(self, payload: LinkRequestPayload) -> tuple[bool, str]:
        """Guarda el mapeo Winamax -> Bet365 para los dos equipos de un partido."""
        async with self._lock:
            changed = upsert_match_team_mapping(
                source_site="winamax",
                source_home_team=payload.winamax_match.home_team,
                source_away_team=payload.winamax_match.away_team,
                canonical_home_team=payload.bet365_match.home_team,
                canonical_away_team=payload.bet365_match.away_team,
                mappings=self._team_name_mappings,
            )

            if not changed:
                return False, "El enlace ya estaba guardado."

            await asyncio.to_thread(
                save_team_name_mappings,
                self._mappings_path,
                self._team_name_mappings,
            )

        return True, "Enlace guardado en team_name_mappings.json"


def load_dashboard_assets(config: DashboardServerConfig) -> DashboardAssets:
    """Carga en memoria plantilla HTML y recursos estáticos."""
    return DashboardAssets(
        template=config.template_path.read_text("utf-8"),
        css=config.css_path.read_text("utf-8"),
        js=config.js_path.read_text("utf-8"),
    )


def build_dashboard_url(config: DashboardServerConfig) -> str:
    """Construye la URL del dashboard local."""
    return f"http://{config.host}:{config.port}/"


def build_dashboard_view_url(config: DashboardServerConfig, view_mode: str) -> str:
    """Construye la URL de una vista concreta del dashboard."""
    return f"http://{config.host}:{config.port}/{view_mode}"


def open_dashboard_window(config: DashboardServerConfig) -> None:
    """Abre una nueva ventana con el dashboard local servido por HTTP."""
    webbrowser.open_new(build_dashboard_url(config))


def open_dashboard_windows(config: DashboardServerConfig) -> None:
    """Abre dos ventanas: una para enlazar y otra para partidos enlazados."""
    webbrowser.open_new(build_dashboard_view_url(config, "linker"))
    webbrowser.open_new(build_dashboard_view_url(config, "linked"))


def _http_response(
    status_code: int,
    reason: str,
    content_type: str,
    body: bytes,
) -> bytes:
    headers = [
        f"HTTP/1.1 {status_code} {reason}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body)}",
        "Connection: close",
    ]
    return ("\r\n".join(headers) + "\r\n\r\n").encode("utf-8") + body


def _normalize_request_path(path: str) -> str:
    """Normaliza la ruta HTTP para comparar endpoints de forma robusta."""
    parsed = urlsplit(path)
    normalized_path = parsed.path or "/"
    if normalized_path != "/":
        normalized_path = normalized_path.rstrip("/")
    return normalized_path or "/"


async def start_dashboard_server(
    state: DashboardState,
    config: DashboardServerConfig,
    assets: DashboardAssets,
) -> asyncio.Server:
    """Levanta servidor HTTP local para dashboard y endpoint de enlace."""

    async def handle_client(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            request_head = await reader.readuntil(b"\r\n\r\n")
        except asyncio.IncompleteReadError, asyncio.LimitOverrunError:
            writer.close()
            await writer.wait_closed()
            return

        header_bytes, _, buffered_body = request_head.partition(b"\r\n\r\n")
        header_text = header_bytes.decode("utf-8", errors="ignore")
        header_lines = header_text.split("\r\n")
        if not header_lines:
            writer.close()
            await writer.wait_closed()
            return

        request_parts = header_lines[0].split(" ")
        if len(request_parts) < 2:
            response = _http_response(
                400,
                "Bad Request",
                "application/json; charset=utf-8",
                b'{"message":"Solicitud invalida"}',
            )
            writer.write(response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        method = request_parts[0].upper()
        path = _normalize_request_path(request_parts[1])

        headers: dict[str, str] = {}
        for line in header_lines[1:]:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

        content_length = int(headers.get("content-length", "0"))
        body = buffered_body
        if content_length > len(body):
            body += await reader.readexactly(content_length - len(body))

        response: bytes
        if method == "GET" and path in {"/", "/index.html", "/linked", "/linker"}:
            if path == "/linked":
                view_mode = "linked"
            elif path == "/linker":
                view_mode = "linker"
            else:
                view_mode = "all"

            html_content = await state.get_html()
            html_with_mode = html_content.replace("__VIEW_MODE__", view_mode)
            response = _http_response(
                200,
                "OK",
                "text/html; charset=utf-8",
                html_with_mode.encode("utf-8"),
            )
        elif method == "GET" and path == "/src/ui/dashboard.css":
            response = _http_response(
                200,
                "OK",
                "text/css; charset=utf-8",
                assets.css.encode("utf-8"),
            )
        elif method == "GET" and path == "/src/ui/dashboard.js":
            response = _http_response(
                200,
                "OK",
                "application/javascript; charset=utf-8",
                assets.js.encode("utf-8"),
            )
        elif method == "POST" and path == "/api/link":
            try:
                content_type = headers.get("content-type", "").split(";", 1)[0].strip()
                if content_type and content_type != "application/json":
                    response = _http_response(
                        400,
                        "Bad Request",
                        "application/json; charset=utf-8",
                        b'{"message":"Payload invalido: se esperaba JSON (Content-Type: application/json)"}',
                    )
                    writer.write(response)
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
                    return

                payload = LinkRequestPayload.model_validate_json(body)
                changed, message = await state.link_matches(payload)
                response_body = json.dumps(
                    {
                        "ok": changed,
                        "message": message,
                    },
                    ensure_ascii=False,
                ).encode("utf-8")
                response = _http_response(
                    200,
                    "OK",
                    "application/json; charset=utf-8",
                    response_body,
                )
            except ValidationError:
                response = _http_response(
                    400,
                    "Bad Request",
                    "application/json; charset=utf-8",
                    b'{"message":"Payload invalido"}',
                )
            except Exception as error:  # noqa: BLE001
                logger.exception(f"Error guardando enlace manual: {error}")
                response = _http_response(
                    500,
                    "Internal Server Error",
                    "application/json; charset=utf-8",
                    b'{"message":"No se pudo guardar el enlace"}',
                )
        else:
            response = _http_response(
                404,
                "Not Found",
                "application/json; charset=utf-8",
                b'{"message":"Ruta no encontrada"}',
            )

        writer.write(response)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(
        handle_client,
        host=config.host,
        port=config.port,
    )
    logger.info(f"Dashboard HTTP disponible en {build_dashboard_url(config)}")
    return server
