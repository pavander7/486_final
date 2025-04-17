from search.db_utils import get_reports
from search.text_utils import create_synthetic_text
from es_utils import index_to_elasticsearch, init_es, embed_text

def main():
    print("Initializing index")
    init_es()

    print("Fetching reports...")
    reports = get_reports(limit=1000)  # for testing

    print("Generating synthetic text...")
    for report in reports:
        synthetic_text = create_synthetic_text(report)
        embedding = embed_text(synthetic_text)
        index_to_elasticsearch(report["reportid"], synthetic_text, embedding)

    print("Done indexing!")

if __name__ == "__main__":
    main()
