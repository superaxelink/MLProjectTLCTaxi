"""Tests para transform_yellow."""
import pandas as pd
import pytest

from pipelines.transform import transform_yellow
from pipelines.config import TAXI_SCHEMAS


def test_transform_dropea_flex_fare():
    """Las filas con payment_type=0 (Flex Fare) deben excluirse."""
    # Arrange: df pequeño con una fila Flex Fare → prepara los datos y el contexto
    df = pd.DataFrame({
        'VendorID': [1, 1, 2],
        'tpep_pickup_datetime': [
            '2026-03-01 10:00:00',
            '2026-03-01 11:00:00',
            '2026-03-01 12:00:00',
        ],
        'tpep_dropoff_datetime': [
            '2026-03-01 10:30:00',
            '2026-03-01 11:30:00',
            '2026-03-01 12:30:00',
        ],
        'payment_type': [1, 0, 2],          # ← el del medio es Flex Fare
        'passenger_count': [1, 2, 3],
        'trip_distance': [1.5, 2.0, 3.0],
        'fare_amount': [10.0, 15.0, 20.0],
    })
    
    # Act  → ejecuta la acción que quieres probar
    result = transform_yellow(df, TAXI_SCHEMAS['yellow'])
    
    # Assert  → verifica que el resultado es el esperado
    assert len(result) == 2, f"Esperaba 2 filas, obtuve {len(result)}"
    assert 0 not in result['payment_type'].values, "Flex Fare no fue excluido"