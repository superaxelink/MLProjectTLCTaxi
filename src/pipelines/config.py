import logging
import os
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

TAXI_SCHEMAS = {
    'yellow': {
        'datetime_cols': ['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
        'critical_cols': ['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
        # Considerar reducir tamañó a futuro
        'int_cols': {'vendorid': 'int16', 'pulocationid': 'int32', 'dolocationid': 'int32', 
                     'payment_type': 'int16', 'passenger_count': 'int8', 'ratecodeid': 'int8'},
        'float_cols': ['trip_distance', 'fare_amount', 'extra', 'mta_tax', 'tip_amount', 'tolls_amount', 
                       'improvement_surcharge', 'total_amount', 'congestion_surcharge', 'airport_fee', 
                       'cbd_congestion_fee'],
        'categorical_cols': ['store_and_fwd_flag'],
        'fill_defaults': {
                # Categóricas / conteos
                'passenger_count': 0, # Decisión: si falta, asume 0 (aunque sea viaje sin pasajeros registrados)
                'ratecodeid': 1, # Decisión: rate code por defecto = 1 (Standard rate)
                # Flag de store-and-forward
                'store_and_fwd_flag': 'N',   # Decisión: asumir "no store and forward" (tu razonamiento)
                # Montos y distancias (todos con default 0)
                'trip_distance': 0.0,
                'fare_amount': 0.0,
                'extra': 0.0,
                'mta_tax': 0.0,
                'tip_amount': 0.0,
                'tolls_amount': 0.0,
                'improvement_surcharge': 0.0,
                'total_amount': 0.0,
                'congestion_surcharge': 0.0,
                'airport_fee': 0.0,
                'cbd_congestion_fee': 0.0,   # Nueva columna desde 2025 [citation:8]
            },
        'exclude_rules': [
            {'column': 'payment_type', 'op': 'eq', 'value': 0, 'reason': 'Flex Fare, out of scope'},
        ]
    },
    # 'green': {},
    # 'fhv': {},
    # 'fhvhv': {}
}

def setup_logging(log_dir: Path=Path('logs'))->None:
    """Configura logging a consola y a archivos con rotacion"""
    log_dir.mkdir(parents=True, exist_ok=True)

    level = os.getenv('LOG_LEVEL','INFO').upper()
    # hora, nombre del registrador,  nivel de gravedad, texto del mensaje
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)

    # Handler de la consola
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    # Handler a archivo con rotación
    file_handler = RotatingFileHandler(
        log_dir / "etl.log",
        maxBytes=10_000_000,  # 10 MB
        backupCount=5,        # Guarda 5 archivos rotados
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # Configurar el root logger
    logging.basicConfig(
        level=level,
        handlers=[console,file_handler],
        force=True, #<- sobreescribe configuracion previa
    )

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

########### COSAS QUE PODRIA IMPLEMENTAR ##############
# Validar que los tipos de taxi en cfg.taxi_types estén en TAXI_SCHEMAS
# Añadir string hardcodeados en variables de entorno o en un archivo de configuración (para no hardcodear en el código) 

# Generates init, getters, setters, repr, eq, and hash methods automatically
# frozen=True makes the dataclass immutable, meaning that its attributes cannot be modified after instantiation.
@dataclass(frozen=True)
class Config:
    #raw_data_dir: Path = Path('data/raw')
    raw_data_dir: Path = PROJECT_ROOT / os.getenv("RAW_DATA_DIR", "data/raw")
    #processed_data_dir: Path = Path('data/processed')
    processed_data_dir: Path = PROJECT_ROOT / os.getenv("PROCESSED_DATA_DIR","data/processed")
    #base_url: str = 'https://d37ci6vzurychx.cloudfront.net/trip-data'
    base_url: str = os.getenv("BASE_URL","https://d37ci6vzurychx.cloudfront.net/trip-data")
    #raw_data_dir: Path = Path('../data/raw')
    #timeout : tuple[int, int] = (10, 60)  # Timeout for HTTP requests in seconds.(connect_timeout, read_timeout)
    timeout : int = int(os.getenv("TIMEOUT","30"))  # Timeout for HTTP requests in seconds.(connect_timeout, read_timeout)
    #chunk_size: int = 1 << 15 # 1 << 15 es "1 desplazado 15 bits a la izquierda" = 2^15 = 32768 
    chunk_size: int = int(os.getenv("CHUNK_SIZE",str(1<<15))) # 1 << 15 es "1 desplazado 15 bits a la izquierda" = 2^15 = 32768 
    taxi_types: tuple = ('yellow', 'green', 'fhv', 'fhvhv')

    #timeout : int = 60  # Timeout for HTTP requests in seconds
    max_workers: int = int(os.getenv("MAX_WORKERS","4"))  # Maximum number of threads for concurrent downloads