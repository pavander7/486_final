import json
import os

import pandas as pd

from config import REPORT_COLS, PATIENT_COLS, REACTION_COLS, DRUG_COLS, DRUGREPORT_COLS, REPORT_BOOL_COLS
from config import SCHEMA_FILEPATH, INPUT_DIR_PATH, POSTGRES_SCHEMA
from helpers import get_db_conn, rename_columns, convert_boolean

def load_json(input_dir):
    """Loads all json files from given input directory."""
    data = []
    
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)

        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as file:
                dump = json.load(file)  # contains 'meta' and 'results'
                results = dump["results"]  # separate the results from the meta
                data.extend(results)
    
    return data

def process_json(data):
    """Processes list of dictionaries to DBMS-friendly format."""
    raw_df = pd.DataFrame(data)

    # PHASE ONE: create tables

    # step 1: select report cols
    reports = raw_df[REPORT_COLS]

    # step 2: select patient cols
    patient_df = pd.json_normalize(raw_df['patient'])
    patient_df = patient_df[PATIENT_COLS]
    reports = pd.concat([reports, patient_df], axis=1)
    
    # step 3: create reactions table
    patient_df = pd.json_normalize(raw_df['patient'])
    patient_df['safetyreportid'] = raw_df['safetyreportid']

    reactions_exploded = patient_df.copy()  # Keep 'patient' data
    reactions_exploded = reactions_exploded.explode('reaction').reset_index(drop=True)
    reactions_normalized = pd.json_normalize(reactions_exploded['reaction'])
    reactions = pd.concat([reactions_exploded.drop(columns=['reaction']), reactions_normalized], axis=1)
    reactions = reactions[REACTION_COLS]

    # step 4: create drugs table
    drugs = pd.json_normalize(patient_df['drug'].explode())
    drugs = rename_columns(drugs, 'openfda.')
    drugs['activesubstance'] = drugs['activesubstance.activesubstancename']
    drugs['administration_route'] = drugs['route']
    drugs = drugs[DRUG_COLS]
    drugs = drugs.drop_duplicates(['activesubstance']).dropna(subset=['activesubstance'])

    # step 5: create drugreports table
    drugreports = patient_df.explode('drug').reset_index(drop=True)
    dr_normalized = pd.json_normalize(drugreports['drug'])
    drugreports = pd.concat([dr_normalized, drugreports.drop(columns=['drug'])], axis=1)
    drugreports['activesubstance'] = drugreports['activesubstance.activesubstancename']
    drugreports = drugreports[DRUGREPORT_COLS]
    drugreports = drugreports.drop_duplicates()

    # PHASE TWO: fix dtypes

    # step 1: fill nans
    reports = reports.where(pd.notnull(reports), None)
    reactions = reactions.where(pd.notnull(reactions), None)
    drugs = drugs.where(pd.notnull(drugs), None)
    drugreports = drugreports.where(pd.notnull(drugreports), None)

    # step 2: booleans
    reports = convert_boolean(reports, REPORT_BOOL_COLS)

    return {'reports': reports, 'reactions': reactions, 'drugs': drugs, 'drugreports': drugreports}

def insert_data(table_name, data):
    """Inserts a Pandas DataFrame into a PostgreSQL table."""
    # Connect to the database
    conn = get_db_conn()
    cur = conn.cursor()

    # Convert NaN/None to None (Postgres will interpret these as NULL)
    data = data.where(pd.notnull(data), None)  # Replaces NaNs with None (NULL in PostgreSQL)

    numeric_columns = data.select_dtypes(include=['float', 'int']).columns
    for col in numeric_columns:
        data[col].apply(pd.to_numeric, errors='coerce')

    # Extract column names from DataFrame
    columns = ', '.join(data.columns)  
    placeholders = ', '.join(['%s'] * len(data.columns))  

    insert_query = f"INSERT INTO openFDA.{table_name} ({columns}) VALUES ({placeholders})"

    # Convert DataFrame to list of tuples
    records = data.itertuples(index=False, name=None)

    # Execute batch insert
    cur.executemany(insert_query, records)

    # Commit and close
    conn.commit()
    cur.close()
    conn.close()

def insert_dr(dr):
    """Inserts the drugreports DataFrame into corresponding PostgreSQL table."""
    # Connect to the database
    conn = get_db_conn()
    cur = conn.cursor()

    # Convert NaN to None (Postgres will interpret these as NULL)
    dr = dr.where(pd.notnull(dr), None)  # Replaces NaNs with None (NULL in PostgreSQL)

    # Step 1: Fetch drugid <-> activesubstance mapping from openFDA.drugs
    cur.execute("SELECT drugid, activesubstance FROM openFDA.drugs;")
    drug_map = pd.DataFrame(cur.fetchall(), columns=['drugid', 'activesubstance'])

    # Step 2: Merge with `dr` to get corresponding drugid
    merged = dr.merge(drug_map, on='activesubstance', how='left')

    # Step 3: Keep only necessary columns
    insert_df = merged[['safetyreportid', 'drugid']].dropna()

    # Convert DataFrame to list of tuples
    records = insert_df.itertuples(index=False, name=None)

    # Step 4: Insert into drugreports
    insert_query = "INSERT INTO openFDA.drugreports (safetyreportid, drugid) VALUES (%s, %s);"
    cur.executemany(insert_query, records)

    # Commit and close
    conn.commit()
    cur.close()
    conn.close()

def init_schema():
    # Delete schema if needed
    drop_schema_if_exists()

    # Connect to the database
    conn = get_db_conn()
    cur = conn.cursor()

    # Read and execute schema file
    with open(SCHEMA_FILEPATH, 'r') as f:
        sql = f.read()

    # Split commands by semicolon and execute each (ignoring empty ones)
    commands = [cmd.strip() for cmd in sql.split(';') if cmd.strip()]
    for command in commands:
        cur.execute(command)

    # Commit changes and close connection
    conn.commit()
    cur.close()
    conn.close()

def drop_schema_if_exists(verbose=True):
    """Drops the specified schema if it exists."""
    conn = get_db_conn()
    cur = conn.cursor()

    # Check if the schema exists
    cur.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name = %s;
    """, (POSTGRES_SCHEMA,))
    
    exists = cur.fetchone()

    if exists:
        # print(f"Schema '{POSTGRES_SCHEMA}' exists — dropping it now")
        cur.execute(f'DROP SCHEMA {POSTGRES_SCHEMA} CASCADE;')
        conn.commit()
        # print(f"Schema '{POSTGRES_SCHEMA}' has been dropped")
    # else:
        # print(f"Schema '{POSTGRES_SCHEMA}' does not exist")

    cur.close()
    conn.close()

def main():
    raw = load_json(INPUT_DIR_PATH)
    print(f'loaded {len(os.listdir(INPUT_DIR_PATH))} files from {INPUT_DIR_PATH}')

    data = process_json(raw)
    print(f'processed {len(data['reports']) + len(data['reactions']) + len(data['drugs']) + len(data['drugreports'])} records')

    dr = data.pop('drugreports')

    init_schema()
    print('executed schema')

    for name, table in data.items():
        insert_data(name, table)
        print(f'inserted {len(table)} records into openFDA.{name}')
    
    insert_dr(dr)
    print(f'inserted {len(dr)} records into openFDA.drugreports')
    
    print('\nDATALOADING COMPLETE.')

if __name__ == "__main__":
    main()