import os
import pandas as pd
import psycopg2 as ps2
import json
import config
from helpers import rename_columns, convert_boolean, convert_numeric

def load_json(input_dir):
    """Loads all json files from given input directory."""
    data = []
    
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)

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
    reports = raw_df[config.REPORT_COLS]

    # step 2: select patient cols
    patient_df = pd.json_normalize(raw_df['patient'])
    patient_df = patient_df[config.PATIENT_COLS]
    reports = pd.concat([reports, patient_df], axis=1)
    
    # step 3: create reactions table
    patient_df = pd.json_normalize(raw_df['patient'])
    patient_df['safetyreportid'] = raw_df['safetyreportid']

    reactions_exploded = patient_df.copy()  # Keep 'patient' data
    reactions_exploded = reactions_exploded.explode('reaction').reset_index(drop=True)
    reactions_normalized = pd.json_normalize(reactions_exploded['reaction'])
    reactions = pd.concat([reactions_exploded.drop(columns=['reaction']), reactions_normalized], axis=1)
    reactions = reactions[config.REACTION_COLS]

    # step 4: create drugs table
    drugs = pd.json_normalize(patient_df['drug'].explode())
    drugs = rename_columns(drugs, 'openfda.')
    drugs['activesubstance'] = drugs['activesubstance.activesubstancename']
    drugs['administration_route'] = drugs['route']
    drugs = drugs[config.DRUG_COLS]

    # step 5: create drugreports table
    drugreports = patient_df.explode('drug').reset_index(drop=True)
    dr_normalized = pd.json_normalize(drugreports['drug'])
    drugreports = pd.concat([dr_normalized, drugreports.drop(columns=['drug'])], axis=1)
    drugreports['activesubstance'] = drugreports['activesubstance.activesubstancename']
    drugreports = drugreports[config.DRUGREPORT_COLS]

    # PHASE TWO: fix dtypes

    # step 1: booleans
    reports = convert_boolean(reports, config.REPORT_BOOL)

    # step 2 numerics
    reports = convert_numeric(reports, config.REPORT_NUM)
    reactions = convert_numeric(reactions, config.REACTION_NUM)
    drugs = convert_numeric(drugs, config.DRUG_NUM)
    drugreports = convert_numeric(drugreports, config.DRUGREPORT_NUM)

    # PHASE THREE: deduplicate
    drugs.drop_duplicates(['activesubstance'])

    return {'reports': reports, 'reactions': reactions, 'drugs': drugs, 'drugreports': drugreports}

def insert_data(table_name, data):
    """Inserts a Pandas DataFrame into a PostgreSQL table."""
    # Connect to the database
    conn = ps2.connect(
        dbname=config.POSTGRES_DBNAME,
        user=config.POSTGRES_USERNAME,
        host=config.POSTGRES_HOSTNAME,
        port=config.POSTGRES_PORT
    )
    cur = conn.cursor()

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
    # Connect to the database
    conn = ps2.connect(
        dbname=config.POSTGRES_DBNAME,
        user=config.POSTGRES_USERNAME,
        host=config.POSTGRES_HOSTNAME,
        port=config.POSTGRES_PORT
    )
    cur = conn.cursor()

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

def run_sql_file(filepath):
    # Connect to the database
    conn = ps2.connect(
        dbname=config.POSTGRES_DBNAME,
        user=config.POSTGRES_USERNAME,
        host=config.POSTGRES_HOSTNAME,
        port=config.POSTGRES_PORT
    )
    cur = conn.cursor()

    # Read and execute schema file
    with open(filepath, 'r') as f:
        sql = f.read()

    # Split commands by semicolon and execute each (ignoring empty ones)
    commands = [cmd.strip() for cmd in sql.split(';') if cmd.strip()]
    for command in commands:
        cur.execute(command)

    # Commit changes and close connection
    conn.commit()
    cur.close()
    conn.close()

def main():
    dump = load_json(config.INPUT_DIR_PATH)
    data = process_json(dump)
    dr = data['drugreports']
    data = data.pop('drugreports')
    run_sql_file(config.SCHEMA_FILEPATH)
    for name, table in data.items():
        insert_data(name, table)
    insert_dr(dr)

if __name__ == "__main__":
    main()