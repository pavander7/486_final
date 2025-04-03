import os
import pandas as pd
import psycopg2 as ps2
import json
import config

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

def extract_key(lst, key):
    return [d.get(key) for d in lst]

def rename_columns(df, prefix):
    """Renames columns starting with 'openfda.' by removing the 'openfda.' prefix."""
    new_columns = {
        col: col.replace(prefix, '') for col in df.columns if col.startswith(prefix)
    }
    df.rename(columns=new_columns, inplace=True)
    return df

def process_json(data):
    """Processes list of dictionaries to DBMS-friendly format."""
    raw_df = pd.DataFrame(data)

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

def main():
    dump = load_json(config.INPUT_DIR_PATH)
    data = process_json(dump)
    for name, table in data.items():
        insert_data(name, table)

if __name__ == "__main__":
    main()