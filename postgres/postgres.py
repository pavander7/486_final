from sys import argv

from config import DEBUG_LIMIT
from downloader import Downloader
from preprocess import process_json, insert_data, insert_dr
from preprocess import init_schema

def main():
    if len(argv > 1) and argv[2] == '-i':
        init_schema()

    dl = Downloader()
    while ((not DEBUG_LIMIT and dl.size()) or (dl.size() <= DEBUG_LIMIT)):
        data = process_json(dl.get())
        dr = data.pop('drugreports')
        for name, table in data.items():
            insert_data(name, table)
        insert_dr(dr)

if __name__ == "__main__":
    main()