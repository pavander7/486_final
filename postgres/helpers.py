import psycopg2
import pandas as pd

from config import POSTGRES_DBNAME, POSTGRES_USERNAME, POSTGRES_HOSTNAME, POSTGRES_PORT

def get_db_conn():
    """Connects to PostgreSQL DB."""
    return psycopg2.connect(
        dbname=POSTGRES_DBNAME,
        host=POSTGRES_HOSTNAME,
        user=POSTGRES_USERNAME,
        port=POSTGRES_PORT
    )

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

def drop_invalid_dict_rows(df, column_name, required_key):
    """
    Drops rows from the DataFrame where:
    - the dictionary in `column_name` is empty
    - `required_key` is missing
    - the value for `required_key` is None, NaN, or an empty list

    Parameters:
    - df: pandas DataFrame
    - column_name: name of the column expected to contain dictionaries
    - required_key: the key that must be present with a valid value

    Returns:
    - A new filtered DataFrame
    """
    def is_valid(d):
        if not isinstance(d, dict) or not d:
            return False
        if required_key not in d:
            return False
        val = d[required_key]
        if val is None or (isinstance(val, float)):
            return False
        if isinstance(val, list) and len(val) == 0:
            return False
        return True

    new_df = df[df[column_name].apply(is_valid)]

    print(f'dropped {len(df) - len(new_df)} out of {len(df)} rows')

    return new_df