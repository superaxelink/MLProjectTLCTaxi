import logging
import pandas as pd
from pipelines.config import TAXI_SCHEMAS

base_path = 'data/raw'
destiny_path = 'data/processed'
date = '2026-03'

#cfg = Config()

#df_raw = pd.read_parquet(f'{cfg.raw_data_dir}/{cfg.taxi_types[0]}_tripdata_{date}.parquet')
# dfg = pd.read_parquet(f'{cfg.base_path}/green_tripdata_{date}.parquet')
# dff = pd.read_parquet(f'{cfg.base_path}/fhv_tripdata_{date}.parquet')
# dfh = pd.read_parquet(f'{cfg.base_path}/fhvhv_tripdata_{date}.parquet')

#df_raw.info()

log = logging.getLogger(__name__)

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# handler = logging.StreamHandler()
# handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
# logger.addHandler(handler)

## Motor de reglas de exclusión

OPS = {
    'eq': lambda s, v: s == v,
    'ne': lambda s, v: s != v,
    'lt': lambda s, v: s < v,
    'le': lambda s, v: s <= v,
    'gt': lambda s, v: s > v,
    'ge': lambda s, v: s >= v,
    'in': lambda s, v: s.isin(v),
    'not_in': lambda s, v: ~s.isin(v),
}

def transform_yellow(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    
    # Transforma el DataFrame de taxi amarillo según el esquema proporcionado.
    
    ### 1. Normalizar nombres de columnas
    # standarize column names: strip whitespace, convert to lowercase, replace spaces with underscores
    df.columns = df.columns.str.strip().str.lower().str.replace(' ','_')

    ### 2. Parsear datetimes
    # These columns are already in datetime format, 
    # but we can convert them to datetime format to ensure consistency and avoid any potential issues with data types. 
    
    for col in schema['datetime_cols']:
        if col in df.columns:
            # En este caso errors='coerce'convierte datos invalidos o mal formateados a NaT (NaN?)(Not a Time), 
            # lo que permite manejar errores de manera más robusta y evita que el proceso falle debido a datos corruptos.
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    ### 3. Drop critical nulls and duplicates
    #log.info(df.info())
    df = df.dropna(subset=schema['critical_cols']).drop_duplicates()
    ### 3.1 Drop rows with payment_type = 0

    for rule in schema.get('exclude_rules', []):
        col = rule['column']
        if col not in df.columns:
            continue
        op = OPS[rule['op']]
        mask = op(df[col], rule['value'])
        before = len(df)
        df = df[~mask]
        log.info("Excluidas %d filas: %s", before - len(df), rule.get('reason', ''))

    ### 4. Fill defaults
    df = df.fillna(value=schema['fill_defaults'])

    ### 5. Cast int_cols
    existing_int = {c: t for c, t in schema['int_cols'].items() if c in df.columns}
    if existing_int:
        df = df.astype(existing_int)

    ### 6. Cast float_cols
    existing_float = [col for col in schema['float_cols'] if col in df.columns]
    if existing_float:
        df[existing_float] = df[existing_float].astype('float64')

    ### 7. Cast categorical_cols
    for col in schema['categorical_cols']:
        if col in df.columns:
            df[col] = df[col].astype('category')
    return df

#df_raw = pd.read_parquet("yellow_tripdata_2024-01.parquet")

# if __name__ == '__main__':
#     from pipelines.config import Config, TAXI_SCHEMAS

#     cfg = Config()
#     date = "2024-01"  # Example date, replace with actual date

#     df_raw = pd.read_parquet(f'{cfg.raw_data_dir}/{cfg.taxi_types[0]}_tripdata_{date}.parquet')

#     print("=== ANTES ===")
#     print(df_raw.dtypes)
#     print(f"Shape: {df_raw.shape}")
#     print(f"Nulos totales: {df_raw.isna().sum().sum()}")
#     print(f"Columnas: {list(df_raw.columns)}")

#     print(df_raw.isna().sum().sort_values(ascending=False))

#     # Queremos saber si hay nulos y por que de estos nulos
#     mask = df_raw['passenger_count'].isna()
#     df_filtrado = df_raw[mask]
#     print(f"\nNulos en passenger_count:")

#     df = transform_yellow(df_raw.copy(), TAXI_SCHEMAS['yellow'])

#     print("\n=== DESPUÉS ===")
#     print(df.dtypes)
#     print(f"Shape: {df.shape}")
#     print(f"Nulos totales: {df.isna().sum().sum()}")
#     print(f"Columnas: {list(df.columns)}")
#     print(f"\nNulos por columna:\n{df.isna().sum()[df.isna().sum() > 0]}")


#     # ¿Algún monto negativo?
#     montos = ['fare_amount', 'tip_amount', 'total_amount', 'tolls_amount']
#     for col in montos:
#         negativos = (df[col] < 0).sum()
#         if negativos:
#             print(f"{col}: {negativos} negativos")

#     # ¿trip_distance negativa o cero?
#     print(f"trip_distance <= 0: {(df['trip_distance'] <= 0).sum()}")

#     # ¿fechas fuera de rango razonable?
#     print(f"pickup min: {df['tpep_pickup_datetime'].min()}")
#     print(f"pickup max: {df['tpep_pickup_datetime'].max()}")

#     # ¿dropoff antes de pickup?
#     invertidos = (df['tpep_dropoff_datetime'] < df['tpep_pickup_datetime']).sum()
#     print(f"Dropoff antes de pickup: {invertidos}")

#     # ¿payment_type fuera de rango esperado (0-6)?
#     print(f"payment_type únicos: {sorted(df['payment_type'].unique())}")

#     # ¿store_and_fwd_flag valores inesperados?
#     print(f"store_and_fwd_flag únicos: {df['store_and_fwd_flag'].unique()}")

#     print(f"Porcentaje: {945748 / len(df_raw) * 100:.2f}%")