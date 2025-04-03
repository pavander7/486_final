import pandas as pd
import json

pd.set_option('display.max_columns', None)

with open("data/drug-event-0001-of-0030.json", "r") as f:
    data = json.load(f)["results"]  # Load raw JSON

reports_df = pd.DataFrame(data)
patients_df = pd.DataFrame(reports_df["patient"].apply(pd.Series))
summaries_df = pd.DataFrame(patients_df["summary"].apply(pd.Series))
reactions_df = pd.DataFrame(patients_df["reaction"].explode().apply(pd.Series))
drugs_df = pd.DataFrame(patients_df["drug"].explode().apply(pd.Series))
activesubstance_df = pd.DataFrame(drugs_df["activesubstance"].apply(pd.Series))

# List of DataFrames and their names
dfs = {
    "Reports": reports_df,
    "Patients": patients_df,
    "Summaries": summaries_df,
    "Reactions": reactions_df,
    "Drugs": drugs_df,
    "Active Substance": activesubstance_df,
}

# Write describe() output to file
with open("summary.txt", "w") as f:
    for name, df in dfs.items():
        f.write(f"=== {name} DataFrame ===\n")
        f.write(df.describe(include="all").to_string())  # Include all types (not just numeric)
        f.write("\n\n")