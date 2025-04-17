import pandas as pd
import requests

from config import LABEL_LINK_FILE, EVENT_LINK_FILE

link_json = requests.get('https://api.fda.gov/download.json').json()
raw = link_json['results']['drug']

label_full = raw['label']

label_df = pd.DataFrame(label_full['partitions'])

label_link = LABEL_LINK_FILE

with open(label_link, 'w', encoding='utf-8') as label_file:
    for link in label_df['file']:
        label_file.write(f'{link}\n')


event_full = raw['event']

event_df = pd.DataFrame(event_full['partitions'])

event_link = EVENT_LINK_FILE

with open(event_link, 'w', encoding='utf-8') as event_file:
    for link in event_df['file']:
        event_file.write(f'{link}\n')