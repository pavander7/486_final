# DATA PATHS
INPUT_DIR_PATH = 'data'
LINK_FILE = 'links.txt'

# COLNAMES FOR PROCESSING
REPORT_COLS =       ['safetyreportid', 'safetyreportversion', 'primarysourcecountry', 'occurcountry', 'transmissiondateformat', 'transmissiondate', 'reporttype', 'serious', 'seriousnessdeath', 'seriousnesslifethreatening', 'seriousnesshospitalization', 'seriousnessdisabling', 'seriousnesscongenitalanomali', 'seriousnessother']
PATIENT_COLS =      ['patientonsetage', 'patientonsetageunit', 'patientsex', 'patientweight', 'patientagegroup'] 
REACTION_COLS =     ['safetyreportid', 'reactionmeddraversionpt', 'reactionmeddrapt', 'reactionoutcome']
DRUG_COLS =         ['drugcharacterization', 'medicinalproduct', 'drugdosagetext', 'drugadministrationroute', 'drugindication', 'actiondrug', 'drugadditional', 'activesubstance', 'application_number', 'brand_name', 'generic_name', 'manufacturer_name', 'product_ndc', 'product_type', 'administration_route', 'substance_name', 'rxcui', 'spl_id', 'spl_set_id', 'package_ndc', 'nui', 'pharm_class_epc', 'pharm_class_moa', 'unii']
DRUGREPORT_COLS =   ['safetyreportid', 'activesubstance']
REPORT_BOOL_COLS =   ['serious', 'seriousnessdeath', 'seriousnesslifethreatening', 'seriousnesshospitalization', 'seriousnessdisabling', 'seriousnesscongenitalanomali', 'seriousnessother']

# POSTGRES AUTH
POSTGRES_DBNAME = 'postgres'
POSTGRES_USERNAME = 'paulvanderwoude'
POSTGRES_HOSTNAME = 'localhost'
POSTGRES_PORT = '5432'
POSTGRES_SCHEMA = "openfda"

# POSTGRES PATHS
SCHEMA_FILEPATH = 'postgres/schema.sql'
DROP_FILEPATH = 'postgres/drop.sql'

# DEBUG TOOLS
DEBUG_LIMIT = None