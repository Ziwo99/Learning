import sqlite3
import pandas as pd
import numpy as np
import traceback
import threading
from datetime import datetime, date


FORBIDDEN_SQL = ['drop', 'delete', 'insert', 'update', 'create', 'alter', 'attach', 'pragma']

SAFE_BUILTINS = {
    '__builtins__': {
        'print': print, 'len': len, 'range': range,
        'list': list, 'dict': dict, 'tuple': tuple,
        'str': str, 'int': int, 'float': float, 'bool': bool,
        'round': round, 'sum': sum, 'min': min, 'max': max,
        'abs': abs, 'sorted': sorted, 'enumerate': enumerate,
        'zip': zip, 'isinstance': isinstance, 'type': type,
        'set': set, 'frozenset': frozenset,
        'True': True, 'False': False, 'None': None,
    }
}


def run_sql(query: str, db_path: str) -> dict:
    normalized = query.strip().lower()
    for word in FORBIDDEN_SQL:
        if normalized.startswith(word) or f' {word} ' in normalized or f'\n{word} ' in normalized:
            return {'error': f"Instruction '{word.upper()}' non autorisée. Seules les requêtes SELECT sont permises."}
    try:
        uri = f'file:{db_path}?mode=ro'
        conn = sqlite3.connect(uri, uri=True)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return _df_to_dict(df)
    except Exception as e:
        return {'error': str(e)}


def run_pandas(code: str, dataframes: dict) -> dict:
    result_container = {}
    error_container = {}

    def _exec():
        safe_globals = dict(SAFE_BUILTINS)
        safe_globals['pd'] = pd
        safe_globals['np'] = np

        local_ns = {name: df.copy() for name, df in dataframes.items()}

        try:
            exec(compile(code, '<user_code>', 'exec'), safe_globals, local_ns)
            result = local_ns.get('result')
            if result is None:
                error_container['error'] = "Assigne ton résultat final à une variable nommée `result`."
                return
            if isinstance(result, pd.DataFrame):
                result_container.update(_df_to_dict(result))
            elif isinstance(result, pd.Series):
                df_result = result.reset_index()
                result_container.update(_df_to_dict(df_result))
            else:
                result_container['scalar'] = str(result)
        except Exception:
            error_container['error'] = traceback.format_exc(limit=6)

    t = threading.Thread(target=_exec)
    t.start()
    t.join(timeout=10)

    if t.is_alive():
        return {'error': "Timeout : l'exécution a dépassé 10 secondes."}
    if error_container:
        return error_container
    return result_container


def _df_to_dict(df: pd.DataFrame) -> dict:
    # Normalize types for JSON serialization
    rows = []
    for row in df.itertuples(index=False):
        normalized = []
        for val in row:
            if pd.isna(val) if not isinstance(val, (list, dict, datetime, date)) else False:
                normalized.append(None)
            elif isinstance(val, (np.integer,)):
                normalized.append(int(val))
            elif isinstance(val, (np.floating,)):
                normalized.append(round(float(val), 6))
            elif isinstance(val, (np.bool_,)):
                normalized.append(bool(val))
            elif isinstance(val, (pd.Timestamp, datetime)):
                normalized.append(str(val)[:10])
            elif isinstance(val, date):
                normalized.append(str(val))
            elif isinstance(val, pd.Period):
                normalized.append(str(val))
            elif not isinstance(val, (str, int, float, bool)):
                normalized.append(str(val))
            else:
                normalized.append(val)
        rows.append(normalized)
    return {
        'columns': list(df.columns),
        'rows': rows,
        'row_count': len(df),
    }
