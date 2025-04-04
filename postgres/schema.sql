CREATE SCHEMA openFDA;

CREATE TABLE openFDA.reports (
    reportid INT PRIMARY KEY,
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
    patientonsetage SMALLINT,
    patientonsetageunit SMALLINT,
    patientsex CHAR(1),
    patientweight SMALLINT,
    patientagegroup SMALLINT
);

CREATE TABLE openFDA.reactions (
    reactionid SERIAL PRIMARY KEY,
    safteyreportid INT NOT NULL,
    reactionmeddraversionpt VARCHAR(10) NOT NULL,
    reactionmeddrapt VARCHAR(50) NOT NULL,
    reactionoutcome SMALLINT,
    FOREIGN KEY (safteyreportid) REFERENCES openFDA.reports(safteyreportid)
);

CREATE TABLE openFDA.drugs (
    drugid SERIAL PRIMARY KEY,
    drugcharacterization SMALLINT,
    medicinalproduct VARCHAR(25),
    drugdosagetext VARCHAR(25),
    drugadministrationroute VARCHAR(25),
    drugindication VARCHAR(25),
    actiondrug SMALLINT,
    drugadditional SMALLINT,
    activesubstance VARCHAR(25) UNIQUE,
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
    unii TEXT[],
    -- there's more info about dosage that i'm not including atm
);

CREATE TABLE openFDA.drugreports (
    drugid INT NOT NULL,
    safteyreportid INT NOT NULL,
    PRIMARY KEY (drugid, safteyreportid)
    FOREIGN KEY (drugid) REFERENCES openFDA.drugs(drugid),
    FOREIGN KEY (safteyreportid) REFERENCES openFDA.reports(safteyreportid)
);