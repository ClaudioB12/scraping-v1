import pandas as pd


def safe_dataframe(data) -> pd.DataFrame:
    """
    Crea un DataFrame garantizando que no haya nombres de columna
    vacios ni duplicados, que son rechazados por pyarrow/Streamlit.
    """
    df = pd.DataFrame(data)
    cols = []
    vistos: dict = {}
    for col in df.columns:
        nombre = str(col).strip() if str(col).strip() else "col"
        if nombre in vistos:
            vistos[nombre] += 1
            nombre = f"{nombre}_{vistos[nombre]}"
        else:
            vistos[nombre] = 0
        cols.append(nombre)
    df.columns = cols
    return df
