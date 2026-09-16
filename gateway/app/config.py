from barmoe_common.config import ConfigBase


class Config(ConfigBase):
    APP_NAME: str = "api-gateway"
    AUTH_URL: str = "http://auth-service:8000"
    PARAMETRIZACION_URL: str = "http://parametrizacion-service:8000"
    TIMEOUT_SEGUNDOS: float = 10.0
    # Carpeta del frontend de Felipe. Vacío = se busca sola (Docker o repositorio).
    FRONTEND_DIR: str = ""
    # IPs de proxies inversos (TLS) delante del gateway cuyo X-Forwarded-For se respeta.
    PROXIES_CONFIABLES: str = ""

    @property
    def proxies_confiables(self) -> set[str]:
        return {p.strip() for p in self.PROXIES_CONFIABLES.split(",") if p.strip()}


config = Config()
