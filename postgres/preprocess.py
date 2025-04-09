import json
import os

import pandas as pd

from config import REPORT_COLS, PATIENT_COLS, REACTION_COLS, DRUG_COLS, DRUGREPORT_COLS, REPORT_BOOL_COLS
from config import LABEL_COLS, OPENFDA_COLS
from config import SCHEMA_FILEPATH, INPUT_DIR_PATH, POSTGRES_SCHEMA
from helpers import get_db_conn, rename_columns, convert_boolean

def load_json(input_dir, prefix=None):
    """Loads all json files from given input directory."""
    data = []
    foo = 'foo'
    
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)

        if file_path.endswith('.json') and (not prefix or file_path.startswith(f'{input_dir}/{prefix}')):
            with open(file_path, 'r', encoding='utf-8') as file:
                dump = json.load(file)  # contains 'meta' and 'results'
                results = dump["results"]  # separate the results from the meta
                data.extend(results)
    
    return data

def process_label_json(data):
    raw_df = pd.DataFrame(data)

    # PHASE ONE: create tables
    raw_df['drugid'] = raw_df['id']

    # step 1: select label cols
    labels = raw_df[LABEL_COLS]

    # step 2: select openfda cols
    openfda = pd.json_normalize(labels['openfda'])
    openfda = pd.concat([labels['drugid'], openfda], axis=1)
    openfda['administration_route'] = openfda['route']
    openfda = openfda[OPENFDA_COLS]

    # PHASE TWO: fix dtypes
    labels = labels.where(pd.notnull(labels), None)
    openfda = openfda.where(pd.notnull(openfda), None)

    # PHASE THREE: join
    labels_full = pd.concat([labels.drop(columns=['openfda'], axis=1), openfda], axis=1)

    return labels_full


def process_event_json(data):
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
    # drugs = pd.json_normalize(patient_df['drug'].explode())
    # drugs = rename_columns(drugs, 'openfda.')
    # drugs['activesubstance'] = drugs['activesubstance.activesubstancename']
    # drugs['administration_route'] = drugs['route']
    # drugs = drugs[DRUG_COLS]
    # drugs = drugs.drop_duplicates(['activesubstance']).dropna(subset=['activesubstance'])

    # step 5: create drugreports table
    drugreports = patient_df.explode('drug').reset_index(drop=True)
    dr_normalized = pd.json_normalize(drugreports['drug'])
    drugreports = pd.concat([dr_normalized, drugreports.drop(columns=['drug'])], axis=1)
    drugreports['spl_id'] = drugreports['openfda.spl_id']
    drugreports = drugreports[DRUGREPORT_COLS]
    # drugreports = drugreports.drop_duplicates()

    # PHASE TWO: fix dtypes

    # step 1: fill nans
    reports = reports.where(pd.notnull(reports), None)
    reactions = reactions.where(pd.notnull(reactions), None)
    # drugs = drugs.where(pd.notnull(drugs), None)
    drugreports = drugreports.where(pd.notnull(drugreports), None)

    # step 2: booleans
    reports = convert_boolean(reports, REPORT_BOOL_COLS)

    return {'reports': reports, 'reactions': reactions, 'drugreports': drugreports}

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
    dr['spl_id'] = dr['spl_id'].apply(
        lambda x: ' '.join(x) if isinstance(x, list) else ('' if pd.isna(x) else str(x))
    )

    # Step 1: Fetch drugid <-> activesubstance mapping from openFDA.drugs
    cur.execute("SELECT drugid, spl_id FROM openFDA.drugs;")
    drug_map = pd.DataFrame(cur.fetchall(), columns=['drugid', 'spl_id'])
    drug_map['spl_id'] = drug_map['spl_id'].apply(
        lambda x: ' '.join(x) if isinstance(x, list) else ('' if pd.isna(x) else str(x))
    )

    # Step 2: Merge with `dr` to get corresponding drugid
    merged = dr.merge(drug_map, on='spl_id', how='left')

    # Step 3: Keep only necessary columns
    insert_df = merged[['safetyreportid', 'drugid']]
    insert_df = insert_df.dropna().drop_duplicates() #remove nas and duplicates

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
    label_raw = load_json(INPUT_DIR_PATH, prefix='drug-label')
    event_raw = load_json(INPUT_DIR_PATH, prefix='drug-event')
    print(f'loaded {len(os.listdir(INPUT_DIR_PATH))} files from {INPUT_DIR_PATH}')

    label_data = process_label_json(label_raw)
    event_data = process_event_json(event_raw)
    print(f'processed {len(label_data) + len(event_data['reports']) + len(event_data['reactions']) + len(event_data['drugreports'])} records')

    dr = event_data.pop('drugreports')

    init_schema()
    print('executed schema')

    insert_data('drugs', label_data)
    print(f'inserted {len(label_data)} records into openFDA.drugs')

    for name, table in event_data.items():
        insert_data(name, table)
        print(f'inserted {len(table)} records into openFDA.{name}')
    
    # insert_dr(dr)
    # print(f'inserted {len(dr)} records into openFDA.drugreports')
    
    print('\nDATALOADING COMPLETE.')

if __name__ == "__main__":
    main()