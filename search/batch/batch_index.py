from sys import argv

from text_utils import create_synthetic_text
from index_utils import index_to_elasticsearch, init_es, embed_text, get_reports, check_init

INDEX_LIMIT_DEFAULT = 1000

def main():
    init = True
    if len(argv) > 1:
        if (len(argv) in [3, 4]) and (argv[1] in ['--limit', '-l'] or argv[2] in ['--limit', '-l']):
            limit = argv[2]
            print(f'index limit set to {limit}')
        elif (len(argv) in [2,4]) and (argv[1] in ['--no_init', '-n'] or argv[3] in ['--no_init', '-n']):
            init = False
            print(f'init disabled')
        else:
            print('USAGE: python search/batch/run_batch_indexing [-l/--limit N]')
            return 1
    else:
        limit = INDEX_LIMIT_DEFAULT
        print(f'index limit not specified, using default={INDEX_LIMIT_DEFAULT}')
    
    if init:
        print("Initializing index")
        init_es()
    elif not check_init():
        print("Overriding --no_init. REASON: index uninitialized.")
        init_es

    print("Fetching reports...")
    reports = get_reports(limit=limit)

    print("Generating synthetic text...")
    for report in reports:
        synthetic_text = create_synthetic_text(report)
        embedding = embed_text(synthetic_text)
        index_to_elasticsearch(report["reportid"], synthetic_text, embedding)

    print("Done indexing!")

if __name__ == "__main__":
    main()
