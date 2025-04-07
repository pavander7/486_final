CREATE SCHEMA openFDA;

CREATE TABLE openFDA.reports (
    safetyreportid INT PRIMARY KEY,
    safetyreportversion SMALLINT,
    primarysourcecountry CHAR(2),
    occurcountry CHAR(2),
    transmissiondateformat SMALLINT,
    transmissiondate DATE,
    reporttype SMALLINT,
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
    patientonsetageunit SMALLINT,
    patientsex SMALLINT,
    patientweight REAL,
    patientagegroup SMALLINT
);

CREATE TABLE openFDA.reactions (
    reactionid SERIAL PRIMARY KEY,
    safetyreportid INT NOT NULL,
    reactionmeddraversionpt VARCHAR(10) NOT NULL,
    reactionmeddrapt TEXT NOT NULL,
    reactionoutcome SMALLINT,
    FOREIGN KEY (safetyreportid) REFERENCES openFDA.reports(safetyreportid)
);

CREATE TABLE openFDA.drugs (
    drugid SERIAL PRIMARY KEY,
    drugcharacterization SMALLINT,
    medicinalproduct TEXT,
    drugdosagetext TEXT,
    drugadministrationroute TEXT,
    drugindication TEXT,
    actiondrug SMALLINT,
    drugadditional SMALLINT,
    activesubstance TEXT UNIQUE,
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
    spl_set_id TEXT[],
    package_ndc TEXT[],
    nui TEXT[],
    pharm_class_epc TEXT[],
    pharm_class_moa TEXT[],
    unii TEXT[]
    -- there's more info about dosage that i'm not including atm
);

CREATE TABLE openFDA.drugreports (
    drugid INT NOT NULL,
    safetyreportid INT NOT NULL,
    PRIMARY KEY (drugid, safetyreportid),
    FOREIGN KEY (drugid) REFERENCES openFDA.drugs(drugid),
    FOREIGN KEY (safetyreportid) REFERENCES openFDA.reports(safetyreportid)
);

CREATE OR REPLACE VIEW openFDA.medications AS (
    SELECT drugid, activesubstance AS med_name, 'substance name' AS source
    FROM openFDA.drugs
    WHERE activesubstance IS NOT NULL AND activesubstance <> ''

    UNION

    SELECT drugid, b AS med_name, 'brand name' AS source
    FROM openFDA.drugs, unnest(brand_name) AS b
    WHERE b IS NOT NULL AND b <> ''

    UNION

    SELECT drugid, g AS med_name, 'generic name' AS source
    FROM openFDA.drugs, unnest(generic_name) AS g
    WHERE g IS NOT NULL AND g <> ''
);
