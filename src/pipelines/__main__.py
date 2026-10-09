import argparse
import logging
from pathlib import Path
import pandas as pd
import sys

from pipelines.config import Config, TAXI_SCHEMAS, setup_logging
from pipelines.extract import extract_data
from pipelines.transform import transform_yellow
from pipelines.load import load

log = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="pipelines", description="Pipeline de taxis NYC")
    p.add_argument("--date", default="2026-03",
                   help="Mes en formato YYYY-MM (default: 2026-03)")
    p.add_argument("--workers", type=int, default=4)
    return p.parse_args()


def main() -> int:
    setup_logging()
    # Extract
    args = parse_args()
    cfg = Config()
    path_list = extract_data(cfg, args.date, max_workers=args.workers)
    log.info("Completado: %d/%d archivos", len(path_list), len(cfg.taxi_types))
    log.info("Extraídas %d filas", len(path_list))
    log.info("Archivos descargados: %s", path_list)

    path, color = path_list['yellow']  # Leer el tercer archivo descargado (taxi amarillo)
    log.info("Leyendo archivo: %s", path)
    #log.info("Leyendo archivo: %s", path[0])

    df_raw = pd.read_parquet(path)  # Leer el tercer archivo descargado (taxi amarillo)
    log.info("Leyendo %d filas", df_raw.shape[0])

    # Transform
    df = transform_yellow(df_raw, TAXI_SCHEMAS['yellow'])
    log.info("Shape final: %s", df.shape)
    log.info("Nulos totales: %d", df.isna().sum().sum())

    # Load
    # Manejadod de esta forma me permite saber donde fallo, sin ocultar bugs
    # Si quisiera loggear a un archivo antes de fallar podria aggregar un exception
    # Tambien serviria para cerrar recursos o borrar archivos temporales.
    # o para hacer retries de forma automatica, o para enviar un email de alerta.
    output_path = Path(f'{cfg.processed_data_dir}/yellow_tripdata_{args.date}.parquet')
    load(df, output_path)

    return 0

########### cOSAS POR IMPLEMENTAR ##############
# Guardar logs en un archivo (ya tienes logging configurado, solo falta agregar un FileHandler)
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('logs/etl.log'),
#         logging.StreamHandler(),  # consola también
#     ]
# )
# Ideal para un VPS
# Añade rotacion para que no crezca indefinidamente. Esto es útil para producción.
# from logging.handlers import RotatingFileHandler
# handler = RotatingFileHandler('logs/etl.log', maxBytes=10_000_000, backupCount=5)
#####################################################

if __name__ == "__main__":
    sys.exit(main())