import requests
import os
import logging
import sys
#import pandas as pd
from .config import Config
from functools import wraps
from pathlib import Path
from datetime import datetime

from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger(__name__)

#BASE_URL = 'https://d37ci6vzurychx.cloudfront.net/trip-data/'
# Caso general
#date = datetime.now().strftime('%Y-%m')  # Get the current date in 'YYYY-MM' format
# Caso de prueba para no descargar muchos datos y saturar mi memoria
#date = '2026-03'
# yellow taxis
# green taxis
# for-hire vehicles (fhv)
# high-volume for-hire vehicles (fhvhv)
#TAXI_TYPES = ['yellow', 'green', 'fhv', 'fhvhv']

# url_yellow = f'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{date}.parquet'
# url_green = f'https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{date}.parquet'
# url_fhv = f'https://d37ci6vzurychx.cloudfront.net/trip-data/fhv_tripdata_{date}.parquet'
# url_hvv = f'https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_{date}.parquet'

def create_url(cfg: Config, taxi_type: str, date: str) -> str:
    return f'{cfg.base_url}/{taxi_type}_tripdata_{date}.parquet'

def create_filepath(cfg: Config, taxi_type: str, date: str) -> str:
    return f'{cfg.raw_data_dir}/{taxi_type}_tripdata_{date}.parquet'

# Devuelve PATH exito, None fallo
def download_file(cfg: Config,taxi_type:str, date:str) -> Path | None:
    destination_path = cfg.raw_data_dir / f'{taxi_type}_tripdata_{date}.parquet' #create_filepath(cfg, taxi_type, date)
    #destination_path = create_filepath(cfg, taxi_type, date)
    if destination_path.exists():
        log.info(f"File {destination_path} already exists. Skipping download.")
        return destination_path
    url = create_url(cfg, taxi_type, date)
    try:
        # requests abre la conexión.
        # Envía la petición.
        # Recibe las cabeceras.
        # NO descarga el cuerpo. Deja la conexión abierta, esperando.
        # Te devuelve el objeto Response con la conexión "en pausa".
        # El cuerpo se descarga bajo demanda, trozo a trozo, al iterar.
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()  # Raise an exception for HTTP errors
            # Ensure the directory exists. 
            # parents=True allows the creation of parent directories if they don't exist 
            # exist_ok=True does nothing if the directory already exists.
            cfg.raw_data_dir.mkdir(parents=True, exist_ok=True)
            # Peligrooso: si la descarga se interrumpe, el archivo puede quedar corrupto.
            # with open(dest, 'wb') as f: 
            #     for chunk in r.iter_content(...):
            #         f.write(chunk)  
            # reemplaza la extension del archivo por .parquet.tmp para evitar problemas si la descarga se interrumpe
            tmp = destination_path.with_suffix('.parquet.tmp')  
            with tmp.open('wb') as f: # destination_path no existe hasta que termine la descarga, por eso se usa tmp.
                # Va cediendo trozos de datos a medida que se descargan, en lugar de cargar todo el archivo en memoria.
                # cada chunk se escribe en disco y se descarta de la memoria, lo que es más eficiente para archivos grandes.
                #for chunk in r.iter_content(chunk_size=8192):
                for chunk in r.iter_content(chunk_size=1 << 15): # 1 << 15 es "1 desplazado 15 bits a la izquierda" = 2^15 = 32768 
                    # = 32768 = 32 KB
                    f.write(chunk)
            tmp.rename(destination_path)  # Rename the temporary file to the final destination
        log.info(f"Downloaded {url} to {destination_path}")
        return destination_path
    # HTTPError	Status 4xx / 5xx (404, 403, 500)
    # ConnectionError	No hay red, DNS falla, host inalcanzable
    # Timeout	Servidor tarda demasiado
    # TooManyRedirects	Bucle de redirects
    # RequestException	Superclase de todas las anteriores
    #except requests.HTTPError as e:
    except requests.RequestException as e:
        log.warning(f"HTTP error occurred while downloading {url}: {e}")
        return None

def extract_data(cfg: Config, date: str, max_workers: int = 4) -> list[Path]:
    answer = []
    # ThreadPoolExecutor creates a pool of threads, allowing for concurrent execution of tasks. 
    # The max_workers parameter specifies the maximum number of threads that can be used simultaneously.
    # with assures all threads are closed and cleaned up correctly when finished.
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        # submit schedules the callable (download_file) to be executed and returns a Future object 
        # representing the execution of the callable.
        # download_file gets called with cfg, taxi_type, and date as arguments.
        # The dictionary comprehension creates a mapping of Future objects to their corresponding taxi types.
        # futures is a dictionary where the keys are Future objects and the values are taxi types.
        futures = {ex.submit(download_file, cfg, t, date): t
                   # download recibe cfg, t, date
                   for t in cfg.taxi_types
                   # los tipos vienen de cfg.taxi_types
                   }
        for future in as_completed(futures):
            path = future.result() # Wait for the future to complete and get the result (the downloaded file path)
            if path:
                answer.append(path)
    return answer

if __name__ == "__main__":
    # sys.argv es una lista que Python rellena automáticamente con los argumentos con los que ejecutaste el script.
    # sys.argv[0] siempre es el nombre del script.
    # sys.argv[1], sys.argv[2], ... son los argumentos que escribiste después.
    # Si no pasas nada, solo existe sys.argv[0].
    log.info(f"sys.argv: {sys.argv}")
    target_date = sys.argv[1] if len(sys.argv) > 1 else '2026-03'
    cfg = Config()                       # Intancia de config
    extract_data(cfg, target_date)       # llamada a extract_data con la fecha objetivo y la configuración

# def get_taxi_data(taxi_type, date):
#     url = create_url(taxi_type, date)
#     response = requests.get(url) # The whole file is downloaded into memory, which may not be efficient for large files.
#     response.raise_for_status()  # Raise an exception for HTTP errors
#     return response.content

# def info_message_decorator(function):
#     @wraps(function)
#     def wrapper(*args, **kwargs):
#         print(f"Starting download attempt with {function.__name__}...")
#         result = function(*args, **kwargs)
#         print(f"Finished download attempt with {function.__name__}.")
#         return result
#     return wrapper

# @info_message_decorator
# def download_save_taxi_data(taxi_type, date):
#     filepath = create_filepath(taxi_type, date)
#     if not os.path.exists(filepath):
#         data = get_taxi_data(taxi_type, date)
#         with open(filepath, 'wb') as f:
#             f.write(data)
#     else:
#         print(f"File {filepath} already exists. Skipping download.")

# def main():
#     print(f"Starting download attempt for taxi data at date: {date}")
#     cfg = Config()
#     for taxi_type in cfg.TAXI_TYPES:
#         download_save_taxi_data(taxi_type, date)

# def main():
#     print(f"Starting download attempt for taxi data at date: {date}")
#     cfg = Config()
#     for taxi_type in cfg.TAXI_TYPES:
#         download_save_taxi_data(taxi_type, date)

#response = requests.get(url)

#df = pd.read_parquet('MLProjectTaxi/data/raw/green_tripdata_2026-03.parquet')

#print(df.head())
#print(df.info())
#print(df.describe())


