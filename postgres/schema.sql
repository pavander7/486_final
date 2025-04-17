CREATE SCHEMA openFDA;

CREATE TABLE openFDA.reports (
    reportid SERIAL PRIMARY KEY,
    safetyreportid TEXT,
    safetyreportversion INT,
    primarysourcecountry CHAR(2),
    occurcountry CHAR(2),
    transmissiondateformat INT,
    transmissiondate DATE,
    reporttype INT,
    serious BOOLEAN,
    seriousnessdeath BOOLEAN,
    seriousnesslifethreatening BOOLEAN,
    seriousnesshospitalization BOOLEAN,
    seriousnessdisabling BOOLEAN,
    seriousnesscongenitalanomali BOOLEAN,
    seriousnessother BOOLEAN,
    -- more dates here, not important
    /*
    receivedateformat SMALLINT,
    receivedate DATE,
    receiptdateformat SMALLINT,
    receiptdate DATE,
    fulfillexpeditecriteria BOOLEAN,
    companynumb VARCHAR(50),
    */
    -- source stuff goes here, going to skip it for now
    patientonsetage REAL,
    patientonsetageunit INT,
    patientsex INT,
    patientweight REAL,
    patientagegroup INT
);

CREATE TABLE openFDA.reactions (
    reactionid SERIAL PRIMARY KEY,
    reportid INT,
    reactionmeddraversionpt VARCHAR(10),
    reactionmeddrapt TEXT,
    reactionoutcome SMALLINT,
    FOREIGN KEY (reportid) REFERENCES openFDA.reports(reportid)
);

CREATE TABLE openFDA.drugs (
    drugid TEXT PRIMARY KEY,
    spl_product_data_elements TEXT[], 
    indications_and_usage TEXT[], 
    dosage_and_administration TEXT[], 
    dosage_forms_and_strengths TEXT[], 
    contraindications TEXT[], 
    warnings_and_cautions TEXT[], 
    adverse_reactions TEXT[], 
    drug_interactions TEXT[], 
    use_in_specific_populations TEXT[], 
    pregnancy TEXT[], 
    pediatric_use TEXT[], 
    geriatric_use TEXT[], 
    overdosage TEXT[], 
    description TEXT[], 
    nonclinical_toxicology TEXT[], 
    carcinogenesis_and_mutagenesis_and_impairment_of_fertility TEXT[], 
    animal_pharmacology_and_or_toxicology TEXT[], 
    information_for_patients TEXT[], 
    package_label_principal_display_panel TEXT[], 
    set_id TEXT, 
    effective_time TEXT, 
    warnings TEXT[], 
    precautions TEXT[], 
    general_precautions TEXT[], 
    storage_and_handling TEXT[], 
    active_ingredient TEXT[], 
    purpose TEXT[], 
    pregnancy_or_breast_feeding TEXT[], 
    keep_out_of_reach_of_children TEXT[], 
    ask_doctor TEXT[], 
    inactive_ingredient TEXT[], 
    other_safety_information TEXT[], 
    boxed_warning TEXT[], 
    nursing_mothers TEXT[], 
    drug_abuse_and_dependence TEXT[], 
    controlled_substance TEXT[], 
    abuse TEXT[], 
    dependence TEXT[], 
    risks TEXT[], 
    labor_and_delivery TEXT[], 
    laboratory_tests TEXT[], 
    teratogenic_effects TEXT[], 
    drug_and_or_laboratory_test_interactions TEXT[], 
    nonteratogenic_effects TEXT[], 
    when_using TEXT[], 
    stop_use TEXT[], 
    do_not_use TEXT[], 
    instructions_for_use TEXT[], 
    ask_doctor_or_pharmacist TEXT[], 
    health_care_provider_letter TEXT[], 
    safe_handling_warning TEXT[], 
    patient_medication_information TEXT[], 
    components TEXT[], 
    intended_use_of_the_device TEXT[], 
    user_safety_warnings TEXT[], 
    cleaning TEXT[], 
    summary_of_safety_and_effectiveness TEXT[], 
    statement_of_identity TEXT[], 
    information_for_owners_or_caregivers TEXT[], 
    veterinary_indications TEXT[], 
    health_claim TEXT[], 
    alarms TEXT[], 
    calibration_instructions TEXT[], 
    application_number TEXT[], 
    brand_name TEXT[], 
    generic_name TEXT[], 
    manufacturer_name TEXT[], 
    product_ndc TEXT[], 
    product_type TEXT[], 
    administration_route TEXT[], 
    substance_name TEXT[], 
    rxcui TEXT[], 
    spl_id TEXT[], 
    spl_id_primary TEXT,
    spl_set_id TEXT[], 
    package_ndc TEXT[], 
    nui TEXT[], 
    pharm_class_epc TEXT[], 
    pharm_class_moa TEXT[], 
    unii TEXT[]
);

CREATE TABLE openFDA.drugreports (
    drugid TEXT NOT NULL,
    reportid INT NOT NULL,
    characterization INT NOT NULL,
    PRIMARY KEY (drugid, reportid),
    FOREIGN KEY (drugid) REFERENCES openFDA.drugs(drugid),
    FOREIGN KEY (reportid) REFERENCES openFDA.reports(reportid)
);

CREATE OR REPLACE VIEW openFDA.medications AS (
    SELECT drugid, b AS med_name, 'brand name' AS source, brand_name, generic_name
    FROM openFDA.drugs, unnest(brand_name) AS b
    WHERE b IS NOT NULL AND b <> ''

    UNION

    SELECT drugid, g AS med_name, 'generic name' AS source, brand_name, generic_name
    FROM openFDA.drugs, unnest(generic_name) AS g
    WHERE g IS NOT NULL AND g <> ''
);

CREATE OR REPLACE VIEW openFDA.med_counts AS (
    SELECT drugid, COUNT(*) AS num_reports
    FROM openFDA.drugreports
    GROUP BY drugid
    ORDER BY num_reports DESC, drugid ASC
);