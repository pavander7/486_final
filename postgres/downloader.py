import requests

from config import LINK_FILE

class Downloader:
    def __init__(self):
        self.links = []
        with open(LINK_FILE, 'r', encoding='utf-8') as file:
            self.links.append(file.readline())
    
    def get(self):
        url = self.links.pop(1)
        response = requests.get(url)
        return response.json()

    def size(self):
        return len(self.links)