import pandas as pd

def rename_columns(df, prefix):
    """Renames columns starting with 'openfda.' by removing the 'openfda.' prefix."""
    new_columns = {
        col: col.replace(prefix, '') for col in df.columns if col.startswith(prefix)
    }
    df.rename(columns=new_columns, inplace=True)
    return df

def convert_boolean (df, colnames, true_val = 2, false_val = 1):
    df = df.copy()
    for col in colnames:
        df[col] = df[col].apply(
            lambda x: True if x == true_val else False if x == false_val else None
        )
    
    return df

def convert_numeric (df, colnames):
    df = df.copy()
    for col in colnames:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df