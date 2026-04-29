import pandas as pd
import numpy as np


def compare_results(user: dict, expected: dict, ordered: bool = False) -> dict:
    if 'error' in user:
        return {'passed': False, 'message': f"Erreur d'exécution : {user['error']}"}
    if 'error' in expected:
        return {'passed': False, 'message': f"Erreur dans la solution de référence : {expected['error']}"}

    # Scalar comparison
    if 'scalar' in expected:
        user_val = user.get('scalar', '')
        return {
            'passed': str(user_val).strip() == str(expected['scalar']).strip(),
            'message': f"Attendu : {expected['scalar']}" if str(user_val).strip() != str(expected['scalar']).strip() else 'Correct !',
        }

    user_cols = set(c.lower() for c in user.get('columns', []))
    exp_cols = set(c.lower() for c in expected.get('columns', []))
    missing = exp_cols - user_cols
    extra = user_cols - exp_cols

    col_errors = []
    if missing:
        col_errors.append(f"Colonnes manquantes : {', '.join(missing)}")
    if extra:
        col_errors.append(f"Colonnes en trop : {', '.join(extra)}")
    if col_errors:
        return {'passed': False, 'message': ' | '.join(col_errors)}

    try:
        user_df = _to_df(user)
        exp_df = _to_df(expected)

        # Reorder user columns to match expected order
        exp_lower = [c.lower() for c in exp_df.columns]
        user_lower_map = {c.lower(): c for c in user_df.columns}
        user_df.columns = [c.lower() for c in user_df.columns]
        user_df = user_df[[c for c in exp_lower if c in user_df.columns]]
        exp_df.columns = [c.lower() for c in exp_df.columns]

        if not ordered:
            user_df = user_df.sort_values(by=list(user_df.columns)).reset_index(drop=True)
            exp_df = exp_df.sort_values(by=list(exp_df.columns)).reset_index(drop=True)

        if len(user_df) != len(exp_df):
            return {
                'passed': False,
                'message': f"Nombre de lignes incorrect : {len(user_df)} obtenues, {len(exp_df)} attendues.",
            }

        # Normalize for comparison
        user_df = _normalize(user_df)
        exp_df = _normalize(exp_df)

        if user_df.equals(exp_df):
            return {'passed': True, 'message': 'Résultat correct !'}

        # Find first difference
        for i, (u_row, e_row) in enumerate(zip(user_df.itertuples(index=False), exp_df.itertuples(index=False))):
            if u_row != e_row:
                return {
                    'passed': False,
                    'message': f"Différence à la ligne {i+1}. Obtenu : {list(u_row)} | Attendu : {list(e_row)}",
                }
        return {'passed': False, 'message': 'Les résultats diffèrent (types ou format).'}

    except Exception as e:
        return {'passed': False, 'message': f"Erreur de comparaison : {e}"}


def _to_df(result: dict) -> pd.DataFrame:
    return pd.DataFrame(result.get('rows', []), columns=result.get('columns', []))


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for col in result.columns:
        try:
            converted = pd.to_numeric(result[col], errors='coerce')
            if not converted.isna().all():
                result[col] = converted
        except Exception:
            pass
        if result[col].dtype == float or result[col].dtype == np.float64:
            result[col] = result[col].round(4)
        if result[col].dtype == object:
            result[col] = result[col].astype(str).str.strip()
    return result
