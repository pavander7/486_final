import requests
import io
import zipfile
import json
import os

class Downloader:
    def __init__(self, file, skip, limit):
        self.links = []
        with open(file, 'r', encoding='utf-8') as file:
            s = 0
            while (s < skip):
                junk = file.readline()
                s += 1
            l = 0
            while (l < limit):
                self.links.append(file.readline())
                l += 1
    
    def get(self):
        url = self.links.pop(0).strip()
        print(url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)' 
                          'AppleWebKit/537.36 (KHTML, like Gecko)' 
                          'Chrome/135.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        
        # Unzip the file in memory
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            json_filename = z.namelist()[0]  # Assuming 1 file inside
            with z.open(json_filename) as f:
                data = json.load(f)['results']  # Convert JSON into Python dict

        print('file downloaded')

        return data


    def size(self):
        return len(self.links)