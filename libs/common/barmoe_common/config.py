"""Configuración base compartida por todos los microservicios.

Cada servicio hereda de ConfigBase y añade lo suyo. Los valores llegan por
variables de entorno o por el archivo .env de la raíz del repositorio.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "barmoe-service"
    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./local.db"

    # --- JWT ---
    JWT_SECRET: str = "cambiar-este-secreto-en-produccion"
    JWT_ALGORITMO: str = "HS256"
    JWT_EXPIRA_MINUTOS: int = 60

    # --- Requisitos no funcionales del tablero ---
    INACTIVIDAD_SEGUNDOS: int = 180      # RNF-03: cierre de sesión a los 3 minutos
    MAX_INTENTOS_LOGIN: int = 3          # RNF-09: bloqueo por reintentos
    PERMITIR_MULTISESION: bool = False   # RNF-10: sesión única
    SLA_SEGUNDOS: float = 2.0            # RNF-02: 2 segundos por transacción

    # --- CORS ---
    ORIGENES_PERMITIDOS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def origenes(self) -> list[str]:
        return [o.strip() for o in self.ORIGENES_PERMITIDOS.split(",") if o.strip()]
