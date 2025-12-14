import json
import os
from typing import List, Dict

class JsonDB:
    def __init__(self, folder="data"):
        self.folder = folder
        if not os.path.exists(folder):
            os.makedirs(folder)

    def _get_path(self, filename):
        return os.path.join(self.folder, filename)

    def load(self, filename) -> List[Dict]:
        path = self._get_path(filename)
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save(self, filename, data: List[Dict]):
        path = self._get_path(filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_record(self, filename, record: Dict):
        data = self.load(filename)
        data.append(record)
        self.save(filename, data)
        return data


db = JsonDB()