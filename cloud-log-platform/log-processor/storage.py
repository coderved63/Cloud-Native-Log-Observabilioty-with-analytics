from pymongo import MongoClient, ASCENDING


class MongoStorage:
    def __init__(self, uri: str, db_name: str = 'logs_db'):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db['logs']
        self.collection.create_index([('timestamp', ASCENDING)])
        print(f"[storage] Connected to MongoDB at {uri}, db={db_name}")

    def insert_log(self, doc: dict):
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def get_logs(self, filter_dict: dict = None, limit: int = 100):
        return list(self.collection.find(filter_dict or {}, limit=limit))
