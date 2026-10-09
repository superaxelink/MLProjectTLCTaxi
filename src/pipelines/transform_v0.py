import pandas as pd
from config import Config

base_path = 'data/raw'
destiny_path = 'data/processed'

date = '2026-03'

cfg = Config()

df = pd.read_parquet(f'{base_path}/{cfg.taxi_types[0]}_tripdata_{date}.parquet')
# dfg = pd.read_parquet(f'{base_path}/green_tripdata_{date}.parquet')
# dff = pd.read_parquet(f'{base_path}/fhv_tripdata_{date}.parquet')
# dfh = pd.read_parquet(f'{base_path}/fhvhv_tripdata_{date}.parquet')

df.info()

TAXI_SCHEMAS = {
    'yellow': {
        'datetime_cols': ['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
        'critical_cols': ['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
        # Considerar reducir tamañó a futuro
        'int_cols': {'vendorid': 'int16', 'pulocationid': 'int32', 'dolocationid': 'int32', 'payment_type': 'int16'},
        'float_cols': ['passenger_count', 'trip_distance', 'ratecodeid', 'fare_amount', 
                       'extra', 'mta_tax', 'tip_amount', 'tolls_amount', 
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
    },
    # 'green': {},
    # 'fhv': {},
    # 'fhvhv': {}
}

def transform_yellow(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    ### 1. Normalizar nombres de columnas
    # standarize column names: strip whitespace, convert to lowercase, replace spaces with underscores
    df.columns = df.columns.str.strip().str.lower().str.replace(' ','_')
    ### 2. Parsear datetimes
    # These columns are already in datetime format, 
    # but we can convert them to datetime format to ensure consistency and avoid any potential issues with data types.
    #
    for col in schema['datetime_cols']:
        if col in df.columns:
                # En este caso errors='coerce'convierte datos invalidos o mal formateados a NaT (NaN?)(Not a Time), 
                # lo que permite manejar errores de manera más robusta y evita que el proceso falle debido a datos corruptos.
            df[col] = pd.to_datetime(df[col], errors='coerce')
    #df[TAXI_SCHEMAS['yellow']['datetime_cols']] = df[TAXI_SCHEMAS['yellow']['datetime_cols']].apply(pd.to_datetime, errors='coerce')
    #df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime']) 
    #df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
    
    ### 3. Drop critical nulls and duplicates
    # Remove rows with missing values in the pickup and dropoff datetime columns in critical columns. 
    # This is important because these columns are essential for any analysis related to trip duration, 
    # time of day, etc. If these values are missing, it can lead to incorrect calculations and insights.
    df = df.dropna(subset=schema['critical_cols']).drop_duplicates()
    #df.drop_duplicates(inplace=True)
    ### 4. Fill defaults
    df = df.fillna(value=schema['fill_defaults'])

    ### 5. Cast int_cols
    # df[TAXI_SCHEMAS['yellow']['critical_cols']] = df[TAXI_SCHEMAS['yellow']['critical_cols']].astype('datetime64[ns]')
    existing_int = {c: t for c, t  in schema['int_cols'].items() if c in df.columns}
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

float_columns = ['passenger_count', 'trip_distance', 'ratecodeid', 'fare_amount', 
                 'extra', 'mta_tax', 'tip_amount', 'tolls_amount',
                 'improvement_surcharge', 'total_amount', 'congestion_surcharge',
                 'airport_fee', 'cbd_congestion_fee']
int_columns = ['vendorid', 'pulocationid', 'dolocationid', 'payment_type']

df[float_columns] = df[float_columns].fillna(0).astype(float)
df[int_columns] = df[int_columns].fillna(0).astype(int)


df.to_parquet(f'{destiny_path}/{cfg.taxi_types[0]}_tripdata_{date}_cleaned.parquet', index=False)

print(df.head())

# print(f"Tamaño CSV: {os.path.getsize('extraido.csv') / 1e6:.1f} MB")

# import pandas as pd
# df = pd.read_csv("extraido.csv")
# print(f"Shape: {df.shape}")
# print(f"Memoria: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")