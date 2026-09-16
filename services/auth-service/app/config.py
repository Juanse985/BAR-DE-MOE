from barmoe_common.config import ConfigBase


class Config(ConfigBase):
    APP_NAME: str = "auth-service"
    DATABASE_URL: str = "postgresql+psycopg2://barmoe:barmoe@postgres:5432/auth_db"

    # Usuario administrador que se crea al arrancar si la tabla está vacía.
    ADMIN_CEDULA: str = "1000000000"
    ADMIN_NOMBRE: str = "Administrador General"
    ADMIN_USUARIO: str = "admin"
    ADMIN_PASSWORD: str = "Admin2026"

    # HU-002 · aporte de Angel: minutos que dura el bloqueo por reintentos.
    # 0 = la cuenta queda bloqueada hasta que el administrador la desbloquee
    # (criterio 4 de HU-002: "debe contactar al administrador").
    BLOQUEO_MINUTOS: int = 0

    # OBS-02 · límite por IP: fallos de login desde una misma IP en la ventana.
    MAX_INTENTOS_POR_IP: int = 10
    VENTANA_IP_MINUTOS: int = 15


config = Config()
