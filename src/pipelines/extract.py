import requests
import logging
import sys
import pandas as pd
from pipelines.config import Config
from functools import wraps
from pathlib import Path
#from datetime import datetime
#from tenacity import {retry, stop_after_attempt, wait_exponential, retry_if_exception_type}
from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger(__name__)

def create_url(cfg: Config, taxi_type: str, date: str) -> str:
    return f'{cfg.base_url}/{taxi_type}_tripdata_{date}.parquet'

def create_filepath(cfg: Config, taxi_type: str, date: str) -> Path:
    return cfg.raw_data_dir / f'{taxi_type}_tripdata_{date}.parquet'

def _validate_parquet(path: Path) -> bool:
    try:
        pd.read_parquet(path, columns=None).head()
        return True
    except Exception as e:
        log.error(f"El parquet {path} es invalido: {e}")
        return False
    

############# COSAS QUE PODRÍÁ IMPLEMENTAR ########################
# Reintentos con backoff exponencial en download_file (ya tienes tenacity comentado, úsalo)
# Fallo explícito si un archivo crítico no se pudo extraer (no seguir con datos incompletos)
# Exit code correcto en __main__.py (0 si todo ok, 1 si algo falló)
################################################################

# @retry(
#     stop=stop_after_attempt(3),
#     wait=wait_exponential(multiplier=2, min=1, max=30),
#     retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
#     reraise=True
# )
def download_file(cfg: Config,taxi_type:str, date:str) -> Path | None:# Devuelve PATH exito, None fallo
    destination_path = create_filepath(cfg, taxi_type, date) #create_filepath(cfg, taxi_type, date)
    #destination_path = create_filepath(cfg, taxi_type, date)
    if destination_path.exists():
        log.info(f"File {destination_path} already exists. Skipping download.")
        return destination_path, taxi_type
    url = create_url(cfg, taxi_type, date)
    try:
        # requests abre la conexión.
        # Envía la petición.
        # Recibe las cabeceras.
        # NO descarga el cuerpo. Deja la conexión abierta, esperando.
        # Te devuelve el objeto Response con la conexión "en pausa".
        # El cuerpo se descarga bajo demanda, trozo a trozo, al iterar.
        with requests.get(url, stream=True, timeout=cfg.timeout) as r:
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
            #tmp = destination_path.with_suffix('.parquet.tmp')  # No puedo cambiar la extension porque el nombre del archivo ya tiene .parquet, asi que uso with_name para cambiar el nombre completo.
            tmp = destination_path.with_name(destination_path.name + '.tmp')  # Independientemente de la extension, le agrego .tmp al final del nombre del archivo.
            with tmp.open('wb') as f: # destination_path no existe hasta que termine la descarga, por eso se usa tmp.
                # Va cediendo trozos de datos a medida que se descargan, en lugar de cargar todo el archivo en memoria.
                # cada chunk se escribe en disco y se descarta de la memoria, lo que es más eficiente para archivos grandes.
                #for chunk in r.iter_content(chunk_size=8192):
                for chunk in r.iter_content(cfg.chunk_size):  # Usa el chunk_size definido en la configuración
                    # = 32768 = 32 KB
                    f.write(chunk)
            tmp.rename(destination_path)  # Rename the temporary file to the final destination
        log.info(f"Downloaded {url} to {destination_path}")
        #_validate_parquet(destination_path)  # Validate the downloaded parquet file
        if not _validate_parquet(destination_path):
            log.error("Parquet inválido, descartando: %s", destination_path)
            destination_path.unlink()  # borra el archivo corrupto
            return None
        return destination_path, taxi_type
    # HTTPError	Status 4xx / 5xx (404, 403, 500)
    # ConnectionError	No hay red, DNS falla, host inalcanzable
    # Timeout	Servidor tarda demasiado
    # TooManyRedirects	Bucle de redirects
    # RequestException	Superclase de todas las anteriores
    #except requests.HTTPError as e:
    except requests.HTTPError as e:
        # 4xx / 5xx
        log.warning(f"HTTP error {r.status_code} en {url}: {e}")
        return None
    except requests.ConnectionError as e:
        log.warning(f"No se pudo conectar a {url}: {e}")
        return None
    except requests.Timeout as e:
        log.warning(f"Timeout descargando {url}: {e}")
        return None
    except requests.RequestException as e:
        # cualquier otra
        log.warning(f"Error descargando {url}: {e}")
        return None

#def extract_data(cfg: Config, date: str, max_workers: int = 4) -> list[Path]:
def extract_data(cfg: Config, date: str, max_workers: int = 4) -> dict[str, list[Path]]:
    answer = {}
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
            #result = future.result() # Wait for the future to complete and get the result (the downloaded file path)
            # Obténgo el tipo de taxi asociado a este hilo específico
            taxi_type = futures[future] 
            # El resultado es solo el PosixPath del archivo descargado
            path = future.result() 
            if path:
                answer[taxi_type] = path
    return answer

# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s %(levelname)s %(name)s: %(message)s",
#     )
#     # sys.argv es una lista que Python rellena automáticamente con los argumentos con los que ejecutaste el script.
#     # sys.argv[0] siempre es el nombre del script.
#     # sys.argv[1], sys.argv[2], ... son los argumentos que escribiste después.
#     # Si no pasas nada, solo existe sys.argv[0].
#     log.info(f"sys.argv: {sys.argv}")
#     target_date = sys.argv[1] if len(sys.argv) > 1 else '2026-03'
#     cfg = Config()                       # Intancia de config
#     extract_data(cfg, target_date)       # llamada a extract_data con la fecha objetivo y la configuración


