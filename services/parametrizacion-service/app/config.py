from barmoe_common.config import ConfigBase


class Config(ConfigBase):
    APP_NAME: str = "parametrizacion-service"
    DATABASE_URL: str = "postgresql+psycopg2://barmoe:barmoe@postgres:5432/parametrizacion_db"


config = Config()
