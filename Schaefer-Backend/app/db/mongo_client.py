from pymongo import MongoClient

def insert_by_label(uri, db_name, colname, payload):
    client = MongoClient(uri)
    try:
        db   = client[db_name]
        coll = db[colname]

        print(payload)
        doc = { sec['label']: sec['features'] for sec in payload }
        doc['sections'] = list(doc.keys())
        result = coll.insert_one(doc)
        print(f"inserted_id = {result.inserted_id}")
    finally:
        client.close()