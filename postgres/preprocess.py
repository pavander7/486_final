import json
import os

import pandas as pd

from config import REPORT_COLS, PATIENT_COLS, REACTION_COLS, DRUGREPORT_COLS, REPORT_BOOL_COLS
from config import LABEL_COLS, OPENFDA_COLS
from config import SCHEMA_FILEPATH, POSTGRES_SCHEMA
from helpers import get_db_conn, convert_boolean, drop_invalid_dict_rows, convert_age

def process_label_json(data):
    raw_df = pd.DataFrame(data)
    pd.set_option('display.max_rows', None)

    # PHASE ONE: create tables
    raw_df['drugid'] = raw_df['id']
    raw_df = drop_invalid_dict_rows(raw_df, 'openfda', 'spl_id')
    if raw_df.empty:
        return None

    # step 1: select label cols
    labels = raw_df[list(set(LABEL_COLS) & set(raw_df.columns))]

    # step 2: select openfda cols
    openfda = pd.json_normalize(labels['openfda'], errors='ignore')
    openfda['drugid'] = labels['drugid'].reset_index(drop=True)
    openfda['administration_route'] = openfda['route']
    openfda['spl_id_primary'] = openfda['spl_id'].apply(
        lambda x: min(x) if isinstance(x, list) and x else None
    )
    openfda = openfda[OPENFDA_COLS]

    # PHASE TWO: fix dtypes
    # labels = labels.where(pd.notnull(labels), None)
    # openfda = openfda.where(pd.notnull(openfda), None)

    # PHASE THREE: join
    labels_full = pd.merge(openfda, labels.drop(labels=['openfda'], axis=1), on='drugid', how='left')

    return labels_full

def process_event_json(data):
    """Processes list of dictionaries to DBMS-friendly format."""
    raw_df = pd.DataFrame(data)

    # PHASE ONE: create tables

    # step 1: select report cols
    reports = raw_df[list(set(REPORT_COLS) & set(raw_df.columns))]

    # step 2: select patient cols
    patient_df = pd.json_normalize(raw_df['patient'])
    patient_df = convert_age(patient_df)
    patient_df = patient_df[list(set(PATIENT_COLS) & set(patient_df.columns))]
    reports = pd.concat([reports, patient_df], axis=1)
    
    # step 3: create reactions table
    patient_df = pd.json_normalize(raw_df['patient'])
    patient_df['safetyreportid'] = raw_df['safetyreportid']

    reactions_exploded = patient_df.copy()  # Keep 'patient' data
    reactions_exploded = reactions_exploded.explode('reaction').reset_index(drop=True)
    reactions_normalized = pd.json_normalize(reactions_exploded['reaction'])
    reactions = pd.concat([reactions_exploded.drop(columns=['reaction']), reactions_normalized], axis=1)
    reactions = reactions[list(set(REACTION_COLS) & set(reactions.columns))]

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
    drugreports['spl_id_primary'] = drugreports['openfda.spl_id'].apply(
        lambda x: min(x) if isinstance(x, list) and x else None
    )
    drugreports = drugreports[DRUGREPORT_COLS]
    # drugreports = drugreports.drop_duplicates()

    # PHASE TWO: fix dtypes

    # step 1: fill nans
    reports = reports.where(pd.notnull(reports), None)
    reactions = reactions.where(pd.notnull(reactions), None)
    # drugs = drugs.where(pd.notnull(drugs), None)
    drugreports = drugreports.where(pd.notnull(drugreports), None).drop_duplicates()

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
    dr = construct_linked_df(dr)
    dr = dr.where(pd.notnull(dr), None)  # Replaces NaNs with None (NULL in PostgreSQL)

    # Step 1: Fetch drugid <-> activesubstance mapping from openFDA.drugs
    cur.execute("SELECT drugid, spl_id_primary FROM openFDA.drugs;")
    drug_map = pd.DataFrame(cur.fetchall(), columns=['drugid', 'spl_id_primary'])

    # Step 2: Merge with `dr` to get corresponding drugid
    merged = dr.merge(drug_map, on='spl_id_primary', how='left')

    # Step 3: Keep only necessary columns
    insert_df = merged[['reportid', 'drugid']]
    insert_df = insert_df.dropna().drop_duplicates() #remove nas and duplicates

    # Convert DataFrame to list of tuples
    records = insert_df.itertuples(index=False, name=None)

    # Step 4: Insert into drugreports
    insert_query = "INSERT INTO openFDA.drugreports (reportid, drugid) VALUES (%s, %s);"
    cur.executemany(insert_query, records)

    # Commit and close
    conn.commit()
    cur.close()
    conn.close()

def construct_linked_df(df):
    """Inserts the reactions DataFrame into corresponding PostgreSQL table."""
    # Connect to the database
    conn = get_db_conn()
    cur = conn.cursor()

    # Step 1: Fetch drugid <-> activesubstance mapping from openFDA.drugs
    cur.execute("SELECT safetyreportid, MAX(reportid) as relevant_reportid FROM openFDA.reports GROUP BY safetyreportid;")
    report_map = pd.DataFrame(cur.fetchall(), columns=['safetyreportid', 'relevant_reportid'])

    # Step 2: Merge with `dr` to get corresponding drugid
    merged = df.merge(report_map, on='safetyreportid', how='left')

    # Rename reportid column to match schema
    merged['reportid'] = merged['relevant_reportid']

    # Step 3: Keep only necessary columns
    insert_df = merged.drop(['safetyreportid', 'relevant_reportid'], axis=1)

    # Close
    cur.close()
    conn.close()

    return insert_df

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