from barmoe_common.config import ConfigBase


class Config(ConfigBase):
    APP_NAME: str = "parametrizacion-service"
    DATABASE_URL: str = "postgresql+psycopg2://barmoe:barmoe@postgres:5432/parametrizacion_db"
    # HU-023: prefijo del punto de facturación que se imprime antes del consecutivo
    # (0001-0001187, como en el mockup). El consecutivo es único en toda la cadena.
    FACTURA_PREFIJO: str = "0001"


config = Config()
