# DATA PATHS
INPUT_DIR_PATH = 'data'
EVENT_LINK_FILE = 'event_links.txt'
LABEL_LINK_FILE = 'label_links.txt'

# COLNAMES FOR PROCESSING
LABEL_COLS =        ['drugid', 'spl_product_data_elements', 'indications_and_usage', 'dosage_and_administration', 'dosage_forms_and_strengths', 'contraindications', 'warnings_and_cautions', 'adverse_reactions', 'drug_interactions', 'use_in_specific_populations', 'pregnancy', 'pediatric_use', 'geriatric_use', 'overdosage', 'description', 'nonclinical_toxicology', 'carcinogenesis_and_mutagenesis_and_impairment_of_fertility', 'animal_pharmacology_and_or_toxicology', 'information_for_patients', 'package_label_principal_display_panel', 'set_id', 'effective_time', 'openfda', 'warnings', 'precautions', 'general_precautions', 'storage_and_handling', 'active_ingredient', 'purpose', 'pregnancy_or_breast_feeding', 'keep_out_of_reach_of_children', 'ask_doctor', 'inactive_ingredient', 'other_safety_information', 'boxed_warning', 'nursing_mothers', 'drug_abuse_and_dependence', 'controlled_substance', 'abuse', 'dependence', 'risks', 'labor_and_delivery', 'laboratory_tests', 'teratogenic_effects', 'drug_and_or_laboratory_test_interactions', 'nonteratogenic_effects', 'when_using', 'stop_use', 'do_not_use', 'instructions_for_use', 'ask_doctor_or_pharmacist', 'health_care_provider_letter', 'safe_handling_warning', 'patient_medication_information', 'components', 'intended_use_of_the_device', 'user_safety_warnings', 'cleaning', 'summary_of_safety_and_effectiveness', 'statement_of_identity', 'information_for_owners_or_caregivers', 'veterinary_indications', 'health_claim', 'alarms', 'calibration_instructions']
OPENFDA_COLS =      ['application_number', 'brand_name', 'generic_name', 'manufacturer_name', 'product_ndc', 'product_type', 'administration_route', 'substance_name', 'rxcui', 'spl_id', 'spl_set_id', 'package_ndc', 'nui', 'pharm_class_epc', 'pharm_class_moa', 'unii']
REPORT_COLS =       ['safetyreportid', 'safetyreportversion', 'primarysourcecountry', 'occurcountry', 'transmissiondateformat', 'transmissiondate', 'reporttype', 'serious', 'seriousnessdeath', 'seriousnesslifethreatening', 'seriousnesshospitalization', 'seriousnessdisabling', 'seriousnesscongenitalanomali', 'seriousnessother']
PATIENT_COLS =      ['patientonsetage', 'patientonsetageunit', 'patientsex', 'patientweight', 'patientagegroup'] 
REACTION_COLS =     ['safetyreportid', 'reactionmeddraversionpt', 'reactionmeddrapt', 'reactionoutcome']
DRUG_COLS =         ['drugcharacterization', 'medicinalproduct', 'drugdosagetext', 'drugadministrationroute', 'drugindication', 'actiondrug', 'drugadditional', 'activesubstance', 'application_number', 'brand_name', 'generic_name', 'manufacturer_name', 'product_ndc', 'product_type', 'administration_route', 'substance_name', 'rxcui', 'spl_id', 'spl_set_id', 'package_ndc', 'nui', 'pharm_class_epc', 'pharm_class_moa', 'unii']
DRUGREPORT_COLS =   ['safetyreportid', 'spl_id']
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
EVENT_FILE_LIMIT = 3
LABEL_FILE_LIMIT = 3