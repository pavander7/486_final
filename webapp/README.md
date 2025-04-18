# Flask Frontend for Medication Interaction Search

This submodule contains the web frontend of the drug interaction search tool. It allows users to search for medications, view autocomplete suggestions, and submit a list of medications for interaction analysis.

## Structure Overview

```{bash}
webapp/
├── static/                         # Client-side assets
│   ├── script.js                   # JavaScript for autocomplete and dynamic UI
│   └── style.css                   # CSS styles for the app
├── templates/                      # HTML templates (rendered with Jinja2)
│   ├── index.html                  # Homepage UI
│   ├── interaction-results.html    # Placeholder: results display
│   └── medication.html             # Placeholder: individual medication info
├── views/                          # Server-side route handlers
│   ├── __init__.py                 # Blueprint registration
│   ├── index.py                    # Routes for homepage and autocomplete
│   ├── interaction-results.py      # Route logic for results page
│   └── medication.py               # Route logic for medication detail pages
├── __init__.py                     # App factory registration
└── config.py                       # Flask app configuration

```

## Key Features

- **Autocomplete**: Responsive, keyboard-navigable autocomplete for medication names.
- **Medication Selection**: Users can select one or more medications, which are stored in a hidden form input as drug IDs.
- **Form Submission**: Pressing `Ctrl+Enter` or clicking "Submit" sends the list to the server for further processing.
- **Dynamic Suggestions**: Suggestions are sourced in real-time via the `/autocomplete` route using PostgreSQL queries.
- **Tooltips**: Suggestions include source (brand/generic) and show generic/brand names as hover tooltips.

## Routes

### `/`

- Renders the homepage and search interface (`index.html`)

### `/autocomplete`

- Takes a query parameter `q`
- Returns a JSON list of suggestions based on `med_name`
- Queries the `openfda.medications` view in PostgreSQL

### `/interaction-results`

- Takes two parameters: a query `drugs` in the form of a list of `drugid` values, and a list of results `interactions`.
- Renders the search results page (`interaction-results.html`)

### `/medication/<drugid>`

- Takes a medication parameter `drugid`
- Queries the `openfda.drugs` tables in PostgreSQL
- Renders the medicaiton info page (`medication.html`)

## Frontend Logic

- **script.js**:
  - Controls fetching and displaying suggestions
  - Tracks selected medications
  - Handles keyboard and mouse interactions for suggestion navigation
- **index.html**:
  - Renders the main UI
  - Includes suggestion box, feedback messages, and selected med list
- **interaction-results.html**
  - Renders the search results UI
  - Includes selected med list, label warnings, and adverse event interactions
- **medication.html**
  - Renders the medication infor UI
  - Includes fda label information and interactions with common medications

## Notes

- Requires an active connection to a PostgreSQL database populated by the `postgres/` package.
- Only the medication selection is implemented in this version; the interaction analysis functionality is stubbed out but scaffolded.

## Quickstart (in context of full app)

1. Ensure your PostgreSQL database is running and loaded.
2. From the root project directory:

   ```flask run```

3. Navigate to [`http://localhost:5000`](http://localhost:5000) to use the interface.
