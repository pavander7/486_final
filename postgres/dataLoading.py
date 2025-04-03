import os
import pandas as pd
import psycopg2 as ps2
import json

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

def process_json(data):
    """Processes list of dictionaries to DBMS-friendly format."""
    raw_df = pd.DataFrame(data)

    # step 1: select report cols
    reports_cols = ['safetyreportversion', 'safetyreportid', 'primarysourcecountry', 
                   'occurcountry', 'transmissiondateformat', 'transmissiondate', 'reporttype', 
                   'serious', 'seriousnessdeath', 'seriousnesslifethreatening', 'seriousnesshospitalization', 
                   'seriousnessdisabling', 'seriousnesscongenitalanomali', 'seriousnessother', 'patient', 'summary']
    reports = raw_df.loc(reports_cols)

    # step 2: select patient cols
    patients_cols = ['patientonsetage', 'patientonsetageunit', 'patientsex', 'patientweight', 'patientagegroup', 'drug', 'reaction'] 
    reports = pd.concat([reports.drop('patient'), 
                         pd.DataFrame(raw_df['patient']).loc(patients_cols)], axis=1)
    reports['drug'] = reports['drug'].apply(extract_key, 'activesubstance')
    reports['drug'] = reports['drug'].apply(extract_key, 'activesubstancename')

    # step 3: select summary cols
    reports['summary'] = reports['summary']['narrativeincludeclinical']
    
    # step 4: create reactions table
    reactions_cols = ['reactionmeddraversionpt', 'reactionmeddrapt', 'reactionoutcome']
    reactions = raw_df['reaction'].explode().loc(reactions_cols)

    # step 5: create drugs table
    drugs_cols = ['drugcharacterization', 'medicinalproduct', 'drugdosagetext', 'drugadministrationroute', 'drugindication',
                  'actiondrug', 'drugadditional', 'activesubstance', 'application_number', 'brand_name', 'generic_name',
                  'manufacturer_name', 'product_ndc', 'product_type', 'route', 'substance_name', 'rxcui', 'spl_id', 'spl_set_id',
                  'package_ndc', 'nui', 'pharm_class_epc', 'pharm_class_moa', 'unii']
    drugs = raw_df['drug'].explode().loc(drugs_cols)
    drugs['activesubstance'] = drugs['activesubstance']['activesubstancename']

    return {'reports': reports, 'reactions': reactions, 'drugs': drugs}

def insert_data(data):
    """Inserts loaded json data into Postgres."""
    # Connect to the database
    conn = ps2.connect(
        dbname="postgres",
        user="paulvanderwoude",
        host="localhost",  # Or your remote host
        port="5432"        # Default PostgreSQL port
    )

    cur = conn.cursor()

    # stuff

    cur.close()
    conn.close()

def main():
    pd.set_option('display.max_columns', None)
    return

if __name__ == "__main__":
    main()