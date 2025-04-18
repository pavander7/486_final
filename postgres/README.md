# FDA Adverse Event and Label Data Ingestion Pipeline

This project provides a streamlined data ingestion pipeline for downloading, processing, and uploading FDA drug label and adverse event report data into a PostgreSQL database. It supports batch downloading of JSON files, parsing relevant fields, cleaning and validating data, and managing PostgreSQL schema initialization and inserts.

## Project Structure

```{bash}
.
├── postgres/
│   ├── config.py
│   ├── downloader.py
│   ├── helpers.py
│   ├── postgres.py
│   ├── preprocess.py
│   ├── schema.sql
│   └── drop.sql
├── event_links.txt
├── label_links.txt
└── linkgen.py
```

## Setup and Configuration

All configuration (file paths, database parameters, and column names) are defined in `config.py`.

Key configuration:

- `LABEL_COLS`, `OPENFDA_COLS`, etc.: Sets of columns extracted from label and event data.
- PostgreSQL credentials and schema settings.

## FDA Download Link Generator

**File**: `linkgen.py`

This utility script fetches the latest download links for FDA **drug labels** and **adverse event reports** from the [openFDA download API](https://api.fda.gov/download.json). It extracts partitioned `.json.zip` file URLs and writes them into two plain text files for batch processing.

- Queries the `https://api.fda.gov/download.json` endpoint.
- Extracts all download URLs from:
  - `drug.label.partitions`
  - `drug.event.partitions`
- Saves these URLs to:
  - `LABEL_LINK_FILE` → typically `data/label_links.txt`
  - `EVENT_LINK_FILE` → typically `data/event_links.txt`

### `linkgen.py` Usage

```python linkgen.py```

## Downloading JSON Data

**File**: `downloader.py`
**Class**: `Downloader`

Functionality:

- Reads a specified number of URLs from a file (`event_links.txt` or `label_links.txt`).
- Downloads and unzips JSON content in memory.
- Returns parsed JSON data from the `'results'` field.

## postgres.py

This is the main driver function. Adding '-i' in the command line will (re)initialize the schema, otherwise the program will assume the database is properly set up. DEBUG_LIMIT in config can be altered to process only a subset of the files.

## Data Preprocessing

**File**: `preprocess.py`

Functions:

- `load_json(input_dir, prefix)`: Load local JSON files.
- `process_label_json(data)`: Converts raw label JSON into a flat dataframe joining `openfda` fields with metadata. Filters out invalid entries.
- `process_event_json(data)`: Processes event reports into separate tables (`reports`, `patients`, `reactions`, and `drugreports`).
- `insert_data(table_name, df)`: Uploads any DataFrame into a corresponding PostgreSQL table.
- `insert_dr(df)`: Special upload for `drugreports`.
- `construct_linked_df(df)`: Transforms reactions table to include linking information (from `safetyreportid`).

## Utility Functions

**File**: `helpers.py`
Includes helper functions:

- `get_db_conn()`: Establishes connection to PostgreSQL.
- `rename_columns(df, prefix)`: Strips prefixes (e.g. `openfda.`) from columns.
- `convert_boolean(df, colnames)`: Standardizes boolean encodings (2=True, 1=False).
- `drop_invalid_dict_rows(df, column, required_key)`: Filters rows missing valid nested dictionary fields.

## Main Pipeline Script

**File**: `postgres.py`
Run this script to initialize schema and populate the PostgreSQL database.

### `postgres.py` Usage

```python postgres/postgres.py [options]```

### CLI Options

- `--init`: Initializes PostgreSQL schema using schema.sql.
- `--label_off`: Skip processing label files.
- `--event_off`: Skip processing event files.
- `--label_limit N`: Number of label files to download (default: 13).
- `--event_limit N`: Number of event files to download (default: 1600).
- `--label_skip N`: Skip N label links.
- `--event_skip N`: Skip N event links.
- `--verbose`: Enable detailed logging.

## PostgreSQL Integration

- Schema setup via `schema.sql`
- Data is inserted into normalized tables: `drugs`, `openfda`, `reports`, `reactions`, `drugreports`.
- Use `DROP` script (`drop.sql`) to reset schema if needed.

## Notes

- The pipeline assumes the structure of FDA's openFDA API output.
- All data is handled in-memory, allowing for easy adjustments and debugging.
- Designed for robustness with basic data validation before insert.
