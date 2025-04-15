# Medication Interaction Lookup System

A web application that helps users understand potential interactions between medications and supplements.

## Features

- Drug interaction lookup for multiple medications
- Detailed summaries of each medication
- Categorization of interactions (harmful/non-harmful)
- Evidence-based explanations with references
- Accessibility features (high contrast, large font, ARIA tags)
- Neural IR-based search for improved accuracy

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database:
- Create a database named 'postgres'
- Update postgres/config.py with your credentials

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the application:
```bash
python app.py
```

## Project Structure

- `webapp/` - Flask application
  - `static/` - CSS, JavaScript, and other static files
  - `templates/` - HTML templates
  - `views/` - Route handlers
  - `models/` - Database models
  - `services/` - Business logic
- `postgres/` - Database configuration and scripts
- `search/` - Search engine implementation
- `data/` - Data processing scripts and raw data

## Data Sources

- FDA Drug Database
- RxNorm
- MedlinePlus
- DrugBank
- PubMed

## License

MIT License 