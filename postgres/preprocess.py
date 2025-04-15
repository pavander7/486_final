import json
import os
import re

import pandas as pd

from config import REPORT_COLS, PATIENT_COLS, REACTION_COLS, DRUGREPORT_COLS, REPORT_BOOL_COLS
from config import LABEL_COLS, OPENFDA_COLS
from config import SCHEMA_FILEPATH, INPUT_DIR_PATH, POSTGRES_SCHEMA
from helpers import get_db_conn, convert_boolean, drop_invalid_dict_rows

def extract_interactions(drug_labels):
    """Extract interactions from drug labels and store them in the drug_interactions table."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Get all drugs with interaction information
    drugs_with_interactions = drug_labels[drug_labels['drug_interactions'].notna()]
    total_drugs = len(drugs_with_interactions)
    print(f"\nStarting interaction extraction for {total_drugs} drugs...")
    
    for idx, (_, drug) in enumerate(drugs_with_interactions.iterrows(), 1):
        if idx % 10 == 0:  # Print progress every 10 drugs
            print(f"Processing drug {idx}/{total_drugs}...")
            
        if not drug['drug_interactions']:
            continue
            
        # Handle both string and list types for drug_interactions
        interaction_texts = []
        if isinstance(drug['drug_interactions'], list):
            interaction_texts = [str(text).lower() for text in drug['drug_interactions'] if text]
        else:
            try:
                # Try to parse as JSON
                interaction_data = json.loads(drug['drug_interactions'])
                if isinstance(interaction_data, dict):
                    interaction_texts = [str(interaction_data).lower()]
                else:
                    interaction_texts = [str(drug['drug_interactions']).lower()]
            except json.JSONDecodeError:
                interaction_texts = [str(drug['drug_interactions']).lower()]
        
        for interaction_text in interaction_texts:
            # Look for other drugs mentioned in the interaction text
            for _, other_drug in drug_labels.iterrows():
                if other_drug['drugid'] == drug['drugid']:
                    continue
                    
                # Check if this drug is mentioned in the interaction text
                drug_names = []
                if isinstance(other_drug['brand_name'], list):
                    drug_names.extend([name.lower() for name in other_drug['brand_name'] if name])
                if isinstance(other_drug['generic_name'], list):
                    drug_names.extend([name.lower() for name in other_drug['generic_name'] if name])
                    
                for name in drug_names:
                    if name and name in interaction_text:
                        # Found an interaction
                        drug1_id = min(drug['drugid'], other_drug['drugid'])
                        drug2_id = max(drug['drugid'], other_drug['drugid'])
                        
                        # Check if this interaction already exists
                        cur.execute("""
                            SELECT id FROM openfda.drug_interactions 
                            WHERE drug1_id = %s AND drug2_id = %s
                        """, (drug1_id, drug2_id))
                        
                        if not cur.fetchone():
                            # Insert new interaction
                            cur.execute("""
                                INSERT INTO openfda.drug_interactions 
                                (drug1_id, drug2_id, severity, description, source, evidence_level)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                drug1_id,
                                drug2_id,
                                'medium',
                                f"Interaction found in {drug['brand_name'][0] if isinstance(drug['brand_name'], list) and drug['brand_name'] else 'Unknown'} label: {interaction_text[:200]}...",
                                "Drug Label",
                                "moderate"
                            ))
                            if idx % 10 == 0:  # Print when we find interactions
                                print(f"Found interaction between {drug['brand_name'][0] if isinstance(drug['brand_name'], list) and drug['brand_name'] else 'Unknown'} and {other_drug['brand_name'][0] if isinstance(other_drug['brand_name'], list) and other_drug['brand_name'] else 'Unknown'}")
    
    conn.commit()
    cur.close()
    conn.close()
    print("\nInteraction extraction complete!")

def load_json(input_dir, prefix=None):
    """Loads all json files from given input directory."""
    data = []
    
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

    # Add ON CONFLICT DO NOTHING for primary key conflicts
    insert_query = f"INSERT INTO openfda.{table_name} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

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

    # Step 1: Fetch drugid <-> activesubstance mapping from openfda.drugs
    cur.execute("SELECT drugid, spl_id_primary FROM openfda.drugs;")
    drug_map = pd.DataFrame(cur.fetchall(), columns=['drugid', 'spl_id_primary'])

    # Step 2: Merge with `dr` to get corresponding drugid
    merged = dr.merge(drug_map, on='spl_id_primary', how='left')

    # Step 3: Keep only necessary columns
    insert_df = merged[['reportid', 'drugid']]
    insert_df = insert_df.dropna().drop_duplicates() #remove nas and duplicates

    # Convert DataFrame to list of tuples
    records = insert_df.itertuples(index=False, name=None)

    # Step 4: Insert into drugreports
    insert_query = "INSERT INTO openfda.drugreports (reportid, drugid) VALUES (%s, %s);"
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

    # Step 1: Fetch drugid <-> activesubstance mapping from openfda.drugs
    cur.execute("SELECT safetyreportid, MAX(reportid) as relevant_reportid FROM openfda.reports GROUP BY safetyreportid;")
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

    event_data['reactions'] = construct_linked_df(event_data['reactions'])

    for name, table in event_data.items():
        insert_data(name, table)
        print(f'inserted {len(table)} records into openFDA.{name}')
    
    insert_dr(dr)
    print(f'inserted {len(dr)} records into openFDA.drugreports')

    print('\nDATALOADING COMPLETE.')

if __name__ == "__main__":
    main()