from sys import argv

from config import EVENT_FILE_LIMIT, LABEL_FILE_LIMIT, EVENT_LINK_FILE, LABEL_LINK_FILE
from downloader import Downloader
from preprocess import process_event_json, process_label_json, insert_data, insert_dr
from preprocess import init_schema

def main():
    if len(argv > 1) and argv[2] == '-i':
        init_schema()

    label_dl = Downloader(LABEL_LINK_FILE)
    while ((not LABEL_FILE_LIMIT and label_dl.size()) or (label_dl.size() <= LABEL_FILE_LIMIT)):
        data = process_label_json(label_dl.get())
        for name, table in data.items():
            insert_data(name, table)
        insert_dr(dr)

    event_dl = Downloader(EVENT_LINK_FILE)
    while ((not EVENT_FILE_LIMIT and event_dl.size()) or (event_dl.size() <= EVENT_FILE_LIMIT)):
        data = process_event_json(event_dl.get())
        dr = data.pop('drugreports')
        for name, table in data.items():
            insert_data(name, table)
        insert_dr(dr)

if __name__ == "__main__":
    main()