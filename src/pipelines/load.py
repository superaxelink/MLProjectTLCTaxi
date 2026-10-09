# src/pipelines/load.py
import logging
from pathlib import Path
import pandas as pd

log = logging.getLogger(__name__)

def load(df: pd.DataFrame, output_path: Path) -> None:
    """Escribe el dataframe a parquet de forma atomica e idempotente. Si el archivo ya existe, lo sobrescribe.
    
        Args:
            df (pd.DataFrame): Dataframe transformado a guardar.
            output_path (Path): Ruta de salida del archivo parquet.   
    
    """

    # 0  Verifica que no este vacio el df
    if df.empty:
        raise ValueError("El dataframe está vacío. No se puede guardar un parquet vacío.")

    # 1. Crear el directorio de salida si no existe
    output_path.parent.mkdir(parents=True, exist_ok=True) # Asegura que el directorio exista

    # 2. Escribir a temporal (A esto algunos le pueden llamar stagging)
    tmp = output_path.with_name(output_path.name + '.tmp')
    df.to_parquet(tmp, index=False)

    # 3. Validar
    df_check = pd.read_parquet(tmp)
    assert len(df_check) == len(df), "El parquet temporal no tiene el mismo número de filas que el dataframe original"

    # 4. Reemplazar automaticamente (a esto algunos pueden llamarle swap)
    tmp.replace(output_path) # replace es atomico en el mismo filesystem, y sobrescribe si existe. Esto asegura idempotencia.
    #tmp.rename(output_path) # Renombra el archivo temporal al nombre final, asegurando atomicidad


    # 5 Loguear
    log.info(f"Dataframe guardado en {output_path} con {len(df)} filas y {len(df.columns)} columnas.")

    return output_path