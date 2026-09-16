import os


def _bool_env(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # En Docker esto llega ya seteado por docker-compose apuntando a Postgres.
    # Si corres suelto sin Docker (ej. para pytest local), cae a SQLite.
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./auth.db")

    # Nombres alineados a los que ya usa tu docker-compose.yml
    secret_key: str = os.getenv("JWT_SECRET", "cambiar-este-secreto-en-produccion")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # HU-002: bloqueo por intentos fallidos
    max_failed_attempts: int = int(os.getenv("MAX_INTENTOS_LOGIN", "3"))
    lockout_minutes: int = int(os.getenv("LOCKOUT_MINUTOS", "15"))

    # HU-004: cierre de sesión por inactividad (tu compose lo maneja en SEGUNDOS, no minutos)
    inactivity_timeout_seconds: int = int(os.getenv("INACTIVIDAD_SEGUNDOS", "1800"))

    # HU-003: sesión única. Tu compose trae PERMITIR_MULTISESION (default false = sesión única)
    permitir_multisesion: bool = _bool_env("PERMITIR_MULTISESION", "false")

    # admin inicial (nombres alineados a tu compose: ADMIN_USUARIO / ADMIN_PASSWORD)
    default_admin_username: str = os.getenv("ADMIN_USUARIO", "admin")
    default_admin_password: str = os.getenv("ADMIN_PASSWORD", "Admin123!")
    default_admin_email: str = os.getenv("ADMIN_EMAIL", "admin@example.com")


settings = Settings()
