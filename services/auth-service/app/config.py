from barmoe_common.config import ConfigBase


class Config(ConfigBase):
    APP_NAME: str = "auth-service"
    DATABASE_URL: str = "postgresql+psycopg2://barmoe:barmoe@postgres:5432/auth_db"

    # Usuario administrador que se crea al arrancar si la tabla está vacía.
    ADMIN_CEDULA: str = "1000000000"
    ADMIN_NOMBRE: str = "Administrador General"
    ADMIN_USUARIO: str = "admin"
    ADMIN_PASSWORD: str = "Admin2026"


config = Config()
