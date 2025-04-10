import argparse
import pandas as pd

from config import EVENT_LINK_FILE, LABEL_LINK_FILE
from downloader import Downloader
from preprocess import process_event_json, process_label_json, insert_data, insert_dr
from preprocess import init_schema

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--init', action="store_true", help="enables init mode")
    parser.add_argument('--label_off', action="store_true", help="disables label input")
    parser.add_argument('--event_off', action="store_true", help="disables event input")
    parser.add_argument('--label_limit', type=int, default=13, help="maximum label files to read")
    parser.add_argument('--event_limit', type=int, default=1600, help="maximum event files to read")
    parser.add_argument('--label_skip', type=int, default=0, help="number of label files to skip")
    parser.add_argument('--event_skip', type=int, default=0, help="number of event files to skip")
    parser.add_argument('--verbose', action="store_true", help="enables verbose output")

    args = parser.parse_args()

    if args.init:
        init_schema()
        if args.verbose:
            print("schema initialized")

    if not args.label_off:
        label_dl = Downloader(LABEL_LINK_FILE, args.label_skip, args.label_limit)
        if args.verbose:
            print(f'label downloader initialized with skip {args.label_skip} and limit {args.label_limit}')
        while (label_dl.size()):
            data = process_label_json(label_dl.get())
            if args.verbose:
                print('file downloaded')
            if isinstance(data, pd.DataFrame):
                insert_data('drugs', data)
                if args.verbose:
                    print('data uploaded')
            elif args.verbose:
                print('No valid data found')

    if not args.event_off:
        event_dl = Downloader(EVENT_LINK_FILE, args.event_skip, args.event_limit)
        if args.verbose:
            print(f'event downloader initialized with skip {args.event_skip} and limit {args.event_limit}')
        while (event_dl.size()):
            data = process_event_json(event_dl.get())
            if args.verbose:
                print('file downloaded')
            dr = data.pop('drugreports')
            for name, table in data.items():
                insert_data(name, table)
            insert_dr(dr)
            if args.verbose:
                print('data uploaded')

if __name__ == "__main__":
    main()