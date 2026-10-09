import pandas as pd
import pytest

from pipelines.load import load

def test_load_escribe_archivo(tmp_path):
    """El archivo se crea con las filas correctas"""
    # Arrange
    df = pd.DataFrame({
        'a':[1,2,3],
        'b':['x','y','z'],
    })
    output = tmp_path / 'output.parquet'

    # Act
    result = load(df,output)

    # Assert
    assert output.exists() ,'El archivo no se creo'
    assert result == output, f'Esperaba {output}, obtuve {result}'

    # Verificar contenido
    df_read = pd.read_parquet(output)
    assert len(df_read) == 3
    assert list(df_read.columns) == ['a','b']

def test_load_crea_directorio(tmp_path):
    df = pd.DataFrame({'a':[1,2,3]})
    output = tmp_path / 'subdir' / 'nested' / 'output.parquet'

    # El directorio aun no existe
    assert not output.parent.exists()

    result = load(df, output)

    assert output.exists(), 'El archivo no se creo'
    assert output.parent.exists(), 'El directorio no se creo'

def test_load_es_idempotente(tmp_path):
    """Correr load dos veces con el mismo df no duplica datos."""
    df = pd.DataFrame({'a': [1, 2, 3]})
    output = tmp_path / 'output.parquet'
    
    # Primera carga
    load(df, output)
    df_after_first = pd.read_parquet(output)
    
    # Segunda carga
    load(df, output)
    df_after_second = pd.read_parquet(output)
    
    # No se duplicaron filas
    assert len(df_after_first) == len(df_after_second) == 3, \
        f"Esperaba 3 filas en ambas cargas, obtuve {len(df_after_first)} y {len(df_after_second)}"
    
    # El contenido es idéntico
    pd.testing.assert_frame_equal(df_after_first, df_after_second)

def test_load_falla_si_df_vacio(tmp_path):
    df = pd.DataFrame() # dataframe vacio
    output = tmp_path / 'output.parquet'

    with pytest.raises(ValueError):
        load(df,output)

    assert not output.exists(), 'No debería escribri archivo si df esta vacio'

# def test_load_es_idempotente(tmp_path):
#     df = pd.DataFrame({'a':[1,2,3]})
#     output = tmp_path / 'output.parquet'
#     output2 = tmp_path / 'subdir' / 'output.parquet'

#     result1 = load(df,output)
#     result2 = load(df,output) 
#     result3 = load(df,output2)

#     assert result1 == result2, 'Diferentes resultados'

#     # Verificar que resultados coincidan
#     df_read1 = pd.read_parquet(output)
#     df_read2 = pd.read_parquet(output2)

#     assert len(df_read1) == len(df_read2)
#     assert df_read1.columns == df_read2.columns

    # Verificar contenido

# def test_load_reemplaza_archivo_existente(tmp_path):