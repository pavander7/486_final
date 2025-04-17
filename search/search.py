# search functions
from functools import reduce
from itertools import combinations
from collections import Counter
from os import abort
import pandas as pd

from postgres.helpers import get_db_conn

def binary_and_search(drugids):
    """Returns reportids of all reports that list all drugs in terms."""
    conn = get_db_conn()
    cursor = conn.cursor()

    sets = []

    for term in drugids:
        query = "SELECT reportid FROM openFDA.drugreports WHERE drugid = %s"
        cursor.execute(query, (term,))
        sets.append(set(cursor.fetchall()))

    results = reduce(lambda x, y: x & y, sets)

    cursor.close()
    conn.close()

    return results

def get_characterizations(reportid, in_drugids):
    """Returns characterization for each drug in reportid"""
    relevant_results = {}
    extra_results = {}

    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT drugid, characterization
        FROM openfda.drugreports
        WHERE reportid = %s
    """, (reportid,))

    info = cursor.fetchall()

    for drugid, char in info:
        if drugid in in_drugids:
            relevant_results[drugid] = char
        else:
            extra_results[drugid] = char

    cursor.execute("""
        SELECT seriousness
        FROM openfda.reports
        WHERE reportid = %s
    """, (reportid,))

    serious = cursor.fetchone()

    return {"in": relevant_results, "out": extra_results, "serious": serious}

def full_binary_search(drugids):
    """Performs a binary AND search for all combinations of drugs in terms."""
    queries = {}
    # Loop through combination sizes from 2 to the size of the list
    for search_size in range(2, len(drugids) + 1):
        combs = [list(c) for c in combinations(drugids, search_size)]
        queries[search_size] = combs

    queries = dict(sorted(queries.items(), key=lambda item: item[0], reverse=True))

    results = []
    reportset = set()

    for search_size, q_list in queries.items():
        for drugids_i in q_list:
            raw_results = binary_and_search(drugids_i)
            for reportid in raw_results:
                entry = {}
                if reportid not in reportset:
                    entry[reportid] = get_characterizations(reportid, drugids_i)
                    reportset.add(reportid)
                    results.append(entry)

    return results

def get_med_info(drugid):
    """Collects medication information from the DB."""
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT generic_name, drug_interactions
        FROM openfda.drugs
        WHERE drugid = %s
    """, (drugid,))

    info_raw = cursor.fetchone()
    if info_raw is None:
        abort(404)

    drugname = None
    generic_name = info_raw[0]
    if generic_name and isinstance(generic_name, list) and len(generic_name) > 0:
        drugname = generic_name[0]
    else:
        abort(500)
    label_warning = info_raw[1]

    cursor.close()
    conn.close()

    return drugname, label_warning

def score_reports(query_results):
    final_results = []

    for info in query_results.values():
        info['char_score'] = sum([3 - i for i in info['in'].values()]) + sum([3 - i for i in info['out'].values()])
        info['char_ratio'] = info['char_score'] / (info['char_score'] + sum([3 - i for i in info['out'].values()]))
        info['r_drug_relevance'] = len(info['in'])/(len(info['in']) + len(info['out']))
        if 1 in info['in'].values():
            info['in_indicator'] = 1
        else:
            info['in_indicator'] = 0
        if 1 in info['out']:
            info['out_indicator'] = 0
        else:
            info['out_indicator'] = 1
        info['indicator'] = (info['in_indicator'] - info['out_indicator'] + 1)/2
        final_results.append(info)
    
    return final_results

def gather_reactions(query_results):
    final_results = []

    conn = get_db_conn()
    cursor = conn.cursor()

    for info in query_results:
        cursor.execute("""
            SELECT reactionmeddrapt, reactionoutcome
            FROM openfda.reactions
            WHERE reportid = %s
            AND reactionoutcome <> 6
            AND reactionoutcome IS NOT NULL
        """, (info['reportid'],))
        raw = cursor.fetchall()

        severity = 0
        reactions = []
        for reaction, outcome in raw:
            severity += outcome - 1
            reactions.append({"reactiontype": reaction, "reactionoutcome": outcome})
        
        info['reactions'] = reactions
        info['severity'] = severity

        final_results.append(info)
    
    cursor.close()
    conn.close()
    
    return final_results

def final_scores(df, num_drugs):
    foo = pd.DataFrame()
    # standardize
    df['q_drug_relevance'] = len(df['in'])/num_drugs
    df['char_score'] = df['char_score']/max(df['char_score'])
    df['severity'] = df['severity']/max(df['severity'])

    # calculate
    df['final_score'] = df['q_drug_relevance'] * (df['serious'] + df['char_score'] + df['char_ratio'] + df['r_drug_relevance'] + df['indicator'] + df['severity'])

    # sort
    df.sort_values(by=['final_score', 'q_drug_relevance', 'indicator', 'serious', 'r_drug_relevance', 'severity', 'char_score', 'char_ratio'], ascending=[False,False,False,False,False,False,False])

    return df

def execute_query(drugids):
    """Executes a query and returns results"""

    reports = final_scores(
        pd.DataFrame(
            gather_reactions(
                score_reports(
                    full_binary_search(drugids)
                )
            )
        ), 
        len(drugids)
    )

    strong_reports = reports[reports['indicator'] == 1]

    # Flatten the list of all reactiontypes from all rows
    reaction_list = strong_reports['reactions'].dropna().explode()
    reaction_types = []

    for reaction in reaction_list:
        if isinstance(reaction, dict) and 'reactiontype' in reaction:
            reaction_types.append(reaction['reactiontype'])

    # Count frequencies
    reaction_summary = pd.Series(Counter(reaction_types)).sort_values(ascending=False).head(10).to_dict()

    serious_reports = sum(strong_reports['serious'] == 1)

    return reports.to_dict(), reaction_summary, len(strong_reports), serious_reports