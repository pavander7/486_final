# FDA Drug Data Pipeline

This project provides a modular system for downloading, processing, and uploading FDA drug data into a PostgreSQL database. It is organized around three main components, each responsible for a specific stage in the pipeline.

## Project Structure

```{bash}
.
├── postgres/         # Data ingestion pipeline
├── search/           # Backend search service (inc. initialization)
├── webapp/           # Frontend webapp
├── app.py            # Webapp driver
├── requirements.txt  # Python requirements
└── .gitignore        # Gitignore
```

## Quickstart

1. **Clone the repository**
    Download the code from git using

    ```{bash}
    git clone https://github.com/pavander7/486_final.git
    cd 486_final
    ```

2. **Install dependencies**
    - Install Python dependencies:
    ```pip install -r requirements.txt```

    - Install PostgreSQL:
    ```brew install postgres```

    - Install ElasticSearch:
    Download directly [here](elastic.co/downloads/elasticsearch).

3. **Create `postgres/auth.py`**
    - Copy `postgres/auth_template.py` and edit the class attributes of Auth to match the details of your PostgreSQL server.

4. **Generate dataset links**
    The dataloader requires a list of links to pull data from. Run `linkgen.py` to populate the requisite files from openFDA.
    ```python linkgen.py```

5. **Populate PostgreSQL**
    - Start the postgres server
    - Use `postgres/postgres.py` to retrieve, process, and insert openFDA data into your database.
    - Recommended usage:
    ```python postgres/postgres.py --init --event_limit 25```
    - WARNING: It is not recommended to run `postgres/postgres.py` without specifying `--event_limit N`.
    - It is not necessary to directly run `postgres/schema.sql` or `postgres/drop.sql`.
    - See `postgres/README.md` for more information on the `postgres/postgres.py` Command Line Interface.

6. **Populate ElasticSearch**
    - Start the ElasticSearch server
    - Use `search/batch/batch_index.py` to initialize the ElasticSearch index and add a batch of data from PSQL.
    ```python search/batch/batch_index.py --limit 1000```

7. **Start Flask Webapp**
    Begin the webapp service using Flask.
    ```Flask run```

## Web Application

After the database and index are populated, a Flask-based web app provides a user interface for submitting queries.

### Features

- **Searchable Drug Label Index**  
  Users can search for medications by name using a type-ahead search bar.
  
- **Medication Detail Pages**  
  Each medication page shows drug label information pulled directly from the PostgreSQL database.

- **Interaction Checker**  
  Users can select multiple medications and view potential drug-drug interactions derived from adverse event co-occurrence data.

### Usage

1. Ensure your database is running and populated.
2. From the project root, start the Flask app:

    ```flask run```

3. Navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser.

## Module Overviews

- [`postgres/`](postgres/): Contains DBMS and dataloader systems for openFDA adverse event and label data.
- [`search/`](search/): Contains initialization and backend logic for SentenceTrnasformer-based ElasticSearch search service.
- [`webapp/`](webapp/): Contains all frontend logic and backend Flask endpoints for the user-facing Flask app.

Each module has its own README with more detailed usage instructions.

## About the Data

This project uses the [FDA's open data API](https://open.fda.gov/data/download/) to retrieve:

- **Drug Labels** (structured product labeling)
- **Adverse Event Reports** (reports of adverse events including patient biometric data, medications, and reported reactions)

These are large, publicly available datasets updated by the FDA.

## Future Development

- Increase complexity, efficiency, and accuracy of search results
- Test and improve the IR system(s) to better make use of the data
- Incorporate further data sources
- Improve styling and accessibility
- Add unit and integration tests
- Improve file structure and organization
- Add further comments and explanations throughout code
