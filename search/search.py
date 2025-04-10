# search functions
from functools import reduce
from itertools import combinations

from postgres.helpers import get_db_conn

def binary_and_search(terms):
    """Returns reportids of all reports that list all drugs in terms."""
    conn = get_db_conn()
    curr = conn.cursor()

    sets = []

    for term in terms:
        query = "SELECT reportid FROM openFDA.drugreports WHERE drugid = %s"
        curr.execute(query, (term + '%',))
        sets.append(set(curr.fetchall()))

    results = reduce(lambda x, y: x & y, sets)

    curr.close()
    conn.close()

    return results

def full_binary_search(terms):
    """Performs a binary AND search for all combinations of drugs in terms."""
    queries = []
    # Loop through combination sizes from 2 to the size of the list
    for search_size in range(2, len(terms) + 1):
        combinations.extend(combinations(terms, search_size))

    results = {}

    for query in queries:
        results[query] = binary_and_search(query)

    return results

def get_med_info(drug):
    """Collects medication information from the DB."""
    conn = get_db_conn()
    curr = conn.cursor()

    # do something here

    curr.close()
    conn.close()

    return

def execute_query(drugs):
    """Executes a query and returns results"""
    results = {}

    conn = get_db_conn()
    curr = conn.cursor()

    # do something here

    curr.close()
    conn.close()

    return results