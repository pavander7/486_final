# search functions
from functools import reduce
from itertools import combinations

from postgres.helpers import get_db_conn

def binary_and_search(terms):
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
    queries = []
    # Loop through combination sizes from 2 to the size of the list
    for search_size in range(2, len(terms) + 1):
        combinations.extend(combinations(terms, search_size))

    results = {}

    for query in queries:
        results[query] = binary_and_search(query)

    return results