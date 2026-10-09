"""Tests para extract."""
import io
from pathlib import Path

from pipelines.extract import create_url, create_filepath, _validate_parquet
from pipelines.config import Config

import pandas as pd

from unittest.mock import patch, MagicMock

def test_create_url():
    """La URL se construye con base_url, taxi_type y date."""
    cfg = Config()
    
    result = create_url(cfg, taxi_type='yellow', date='2026-03')
    
    expected = f'{cfg.base_url}/yellow_tripdata_2026-03.parquet'
    assert result == expected, f"Esperaba {expected}, obtuve {result}"


def test_create_filepath():
    """La ruta se construye con raw_data_dir, taxi_type y date."""
    cfg = Config()
    
    result = create_filepath(cfg, taxi_type='yellow', date='2026-03')
    
    expected = cfg.raw_data_dir / 'yellow_tripdata_2026-03.parquet'
    assert result == expected, f"Esperaba {expected}, obtuve {result}"
    assert isinstance(result, Path), "Debería devolver un Path"

def test_validate_parquet_valido(tmp_path):
    """validate_parquet devuelve True para un parquet válido y False para uno inválido."""
    # Crea un parquet válido
    valid_parquet = tmp_path / 'valid.parquet'
    df_valid = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    df_valid.to_parquet(valid_parquet)
    
    # Crea un archivo no-parquet
    invalid_parquet = tmp_path / 'invalid.parquet'
    invalid_parquet.write_text("Esto no es un parquet")
    
    assert _validate_parquet(valid_parquet) is True, "Debería devolver True para un parquet válido"
    assert _validate_parquet(invalid_parquet) is False, "Debería devolver False para un parquet inválido"

def test_download_file_skip_si_existe(tmp_path):
    """"Si el archivo ya existe, no descarga y devuelve la ruta"""
    from pipelines.extract import download_file
    from pipelines.config import Config

    # Arranque: cfg con tmp_path como raw_data_dir
    cfg = Config(raw_data_dir=tmp_path)

    # Crea el archivo "ya descargado"
    fake_file = tmp_path / 'yellow_tripdata_2026-03.parquet'
    fake_file.write_bytes(b'fake')

    # Act
    result = download_file(cfg, taxi_type='yellow', date='2026-03')

    # Assert
    assert result is not None, "Deberia devolver algo"
    # result es una tupla (path, taxi_type) segun el codigo
    path, taxi_type = result
    assert path == fake_file, f"Esperaba {fake_file}, obtuve {path}"
    assert taxi_type == 'yellow', f"Esperaba 'yellow', obtuve {taxi_type}"

def test_download_file_descarga_exitosa(tmp_path):
    """Una descarga exitosa guarda el archivo"""
    from pipelines.extract import download_file
    from pipelines.config import Config

    # Arranque: cfg con tmp_path como raw_data_dir
    cfg = Config(raw_data_dir=tmp_path)

    # Generar bytes de un parquet válido
    df = pd.DataFrame({'a': [1, 2, 3]})
    buffer = io.BytesIO()
    df.to_parquet(buffer)
    parquet_bytes = buffer.getvalue()

    mock_response = MagicMock()
    # Si alguien llama a raise_for_status devuelve None (no lanza excepcion)
    # En el codigo real raise_for_status() lanza una excepcion si el status code no es 200, 
    # pero aqui simulamos que es exitoso
    mock_response.raise_for_status.return_value = None # No lanza excepcion
    # Pide que cuando alguien llame moock_response.iter_content(...) devuelva la lista [b'chunk1', b'chunk2']  
    # Pues en mi codigo real iter_contet es un generador que devuelve los chunks a medida que se descargan.
    # En el mock, al reemplazarlo por una lista iterable, el for chunk in r.iter_content(...) funcionará igual.
    #mock_response.iter_content.return_value = [[b'chunk1', b'chunk2']] # iter_content.return_value → porque el código hace for chunk in r.iter_content(...)
    mock_response.iter_content.return_value = [parquet_bytes] # iter_content.return_value → porque el código hace for chunk in r.iter_content(...)

    # Mock de requests.get para simular una descarga exitosa
    # Reemplaza requests.get en mi módulo, no en requests
    # se asigna a mock_get el mock de requests.get para poder configurar su comportamiento y verificarlo
    # reemplazo solo dentro del bloque with, fuera de él requests.get sigue funcionando normalmente
    # patch reemplaza el objeto en el modulo donde se usa, no en el módulo original. 
    # Por eso se hace patch('pipelines.extract.requests.get') y no patch('requests.get')
    # Pues llamamos import requests en pipelines.extract y usamos requests.get allí, no en este test.
    with patch('pipelines.extract.requests.get') as mock_get: # patch('pipelines.extract.requests.get') → reemplaza requests.get en mi módulo, no en requests
        # requests.get(url, ...) se llama → devuelve un objeto
        # Ese objeto se usa como context manager (por el with)
        # El with llama a __enter__() en ese objeto
        # El resultado de __enter__() se asigna a r
        # Dentro del with, r es lo que usas
        # Con el mock:
        # mock_get → reemplaza a requests.get
        # mock_get.return_value → lo que devuelve requests.get(...) (el "objeto respuesta")
        # mock_get.return_value.__enter__ → el método __enter__ de ese objeto
        # mock_get.return_value.__enter__.return_value → lo que devuelve __enter__(), o sea, lo que se asigna a r
        mock_get.return_value.__enter__.return_value = mock_response # __enter__ → porque el código usa with requests.get(...) as r

        # Act
        # Aquí se ejecuta download_file de verdad. Pero todas las llamadas a requests están mockeadas. Entonces:
        # destination_path.exists() → False (porque tmp_path está vacío)
        # requests.get(url, ...) → devuelve el mock_get.return_value (el mock)
        # with ... as r → r es mock_response
        # r.raise_for_status() → devuelve None (configurado)
        # r.iter_content(cfg.chunk_size) → devuelve [b'chunk1', b'chunk2']
        # Se escriben los chunks en el archivo .tmp
        # Se renombra a .parquet
        # Se valida con _validate_parquet (esto sí se ejecuta de verdad, pero el archivo es... hmm, b'chunk1chunk2' no es un parquet válido)
        # Se retorna la tupla
        result = download_file(cfg, taxi_type='yellow', date='2026-03')

    # Assert
    assert result is not None, "Deberia devolver algo"
    path, taxi_type = result
    assert path.exists(), f"El archivo {path} debería existir después de la descarga"
    assert path.read_bytes() == parquet_bytes, "El contenido no coincide"

def test_download_file_maneja_timeout(tmp_path):
    """Si la descarga da timeout, devuelve None."""
    from pipelines.extract import download_file
    from pipelines.config import Config
    import requests
    from unittest.mock import patch
    
    cfg = Config(raw_data_dir=tmp_path)
    
    with patch('pipelines.extract.requests.get') as mock_get:
        mock_get.side_effect = requests.Timeout("timeout simulado")
        
        result = download_file(cfg, 'yellow', '2026-03')
    
    assert result is None, "Debería devolver None en timeout"

def test_extract_data_devuelve_dict_con_4_tipos(tmp_path):
    """extract_data llama a download_file para cada tipo y devuelve un dict."""
    from pipelines.extract import extract_data
    from pipelines.config import Config
    from unittest.mock import patch
    from pathlib import Path
    
    cfg = Config(raw_data_dir=tmp_path)
    
    def fake_download(cfg, taxi_type, date):
        return (tmp_path / f"{taxi_type}.parquet", taxi_type)
    
    with patch('pipelines.extract.download_file', side_effect=fake_download):
        result = extract_data(cfg, '2026-03')
    
    assert len(result) == 4
    assert set(result.keys()) == {'yellow', 'green', 'fhv', 'fhvhv'}

def test_download_file_maneja_timeout(tmp_path):
    """Si la descarga da timeout, devuelve None."""
    from pipelines.extract import download_file
    from pipelines.config import Config
    import requests
    from unittest.mock import patch
    
    cfg = Config(raw_data_dir=tmp_path)
    
    with patch('pipelines.extract.requests.get') as mock_get:
        mock_get.side_effect = requests.Timeout("timeout simulado")
        result = download_file(cfg, 'yellow', '2026-03')
    
    assert result is None, "Debería devolver None en timeout"

# La regla general:
# Mockea lo externo (red, APIs, bases de datos). 