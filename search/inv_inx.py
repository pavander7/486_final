# constructs inverted index

from postgres.helpers import get_db_conn

def collect_drugs():
    conn = get_db_conn()
    curr = conn.cursor()

    query = "SELECT drugid FROM openfda.drugs"
    curr.execute(query)

    curr.close()
    conn.close()

    return curr.fetchall()

def construct_inv_idx(drugs):
    idx = {}
    conn = get_db_conn()
    curr = conn.cursor()
    for drug in drugs:
        query = "SELECT safteyreportid FROM openfda.drugreports WHERE drugid = %s"
        curr.execute(query, (drug + '%',))
        response = curr.fetchall()
        idx[drug] = response
    
    curr.close()
    conn.close()

    return idx

def main():
    with open('search/inv_idx.txt', 'w') as file:
        results = construct_inv_idx(
            collect_drugs()
        )
        for drug, docs in results.items():
            line = f'{drug}: {docs.join(', ')}\n'
            file.write(line)

if __name__ == "__main__":
    main()