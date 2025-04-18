# ElasticSearch Backend Search Server for Medication Interaction Search

This module powers semantic search over FDA adverse event reports. It employs a hybrid approach using Elasticsearch for retrieval and PostgreSQL for metadata enrichment and validation.

## File Structure

```{bash}
search/
├── batch/
│   ├── batch_index.py     # Driver script for initializing and populating ElasticSearch index
│   └── index_utils.py     # Utility functions for interfacing with ElasticSearch and PSQL
├── search.py              # Main search service functions
├── search_functions.py    # Search service helper funcitons
└── text_utils.py          # Text processing utility functions
```

## Overview

This service allows users to query for adverse event reports involving specific **drug names**. It returns:

- Reports ranked by semantic relevance,
- Metadata from the FDA reports database (seriousness, reactions),
- A "strong match" flag if the queried drug is listed as a likely cause (characterization = 1),
- The top 10 most common reaction types in relevant results.

## Components

### `search.execute_query(drugnames: List[str])` (function)

Main entry point to the search system.

#### Parameters

- `drugnames`: List of user-entered drug names (case-insensitive).

#### Returns

- `results`: List of report entries enriched with:
  - `reportid`: internal id for adverse event reports
  - `serious`: whether the report was flagged serious
  - `reactions`: list of reported reactions, including FDA-standardized Preferred Term (PT) and outcome
  - `char_match`: whether any of the queried drugs had `characterization = 1` in this report, indicating likely causation
- `n_strong`: count of reports marked as strong matches (`char_match = True`)
- `n_serious_strong`: count of 'strong' reports marked as serious
- `top_reactions`: dict of top 10 `reaction` PTs across 'strong' reports

### `/batch` (submodule)

Batch job driver for populating the ElasticSearch index.

#### Usage

```python search/batch/batch_index.py [-l/--limit N]```

`-l/--limit N`: limit of how many reports to index (default=1000). recommended for testing.

#### Functions

- `index_utils.get_reports(limit: int)`: retrieves a batch of reports and metadata from PSQL for indexing
- `index_utils.init_es()`: initializes `report-embeddings` index
- `index_utils.embed_text(text: str)`: embeds text using SentenceTransformer
- `index_utils.index_to_elasticsearch(report_id: int, synthetic_text: str, embedding: Tensor)`: indexes report `reportid` with fields preprocessed as `synthetic_text` and it's embedding `embedding`
- `batch_index.main()`: driver function to facilitate batch indexing (see Usage above)

### `search_functions.py` (file)

Helper functions for the runtime operations of the search service.

#### Search Functions

- `search_reports(drugnames: List(str), top_k: int)`: interface function for ElasticSearch query processing.
- `get_characterizations(reportid: int)`: retrieves drug characterizations (evaluations provided by the reporter indicating the likelihood of causality for each drug) for report `reportid`.
- `get_drugid_name_mapping()`: retrieves and formats the `openfda.medications` view from PSQL.
- `get_reactions_and_seriousness(reportid: int)`: retrieves `serious` field (boolean evaluation of the seriousness of the adverse event provided by the reporter) and the `reaction`s (from `openfda.reactions`, including `reactionmeddrapt`—the standardized Preferred Term and `reactionoutcome`—an indication of the resolution (or lack thereof) of the reaction)

## Search Flow

### Semantic Search

- Calls `search_reports(drugnames)` from `search_functions.py`
- Uses sentence-transformer embeddings to retrieve relevant reports from Elasticsearch based on synthetic adverse event text.

### Drug Mapping

- Looks up internal `drugid`s for the user-entered drug names via `openfda.medications`.

### Characterization Check

- For each result, fetches all `(drugid, characterization)` pairs from `openfda.drugreports`.
- Flags a **strong match** if one of the queried drugids has `characterization = 1`.

### Metadata Enrichment

- For each report:
  - `seriousness` from `openfda.reports`
  - `reactions` from `openfda.reactions`
  - `drugs` from `openfda.drugs`
- Reaction outcome 6 (no/unknown outcome) is excluded.

### Summary Statistics

- Aggregates reaction types across all strong reports
- Evaluates risk based on prevalence of strong and serious reports
- Returns top 10 most frequent reactions
