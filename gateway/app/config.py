from barmoe_common.config import ConfigBase


class Config(ConfigBase):
    APP_NAME: str = "api-gateway"
    AUTH_URL: str = "http://auth-service:8000"
    PARAMETRIZACION_URL: str = "http://parametrizacion-service:8000"
    TIMEOUT_SEGUNDOS: float = 10.0


config = Config()
