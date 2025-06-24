import weaviate

client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=weaviate.classes.init.AdditionalConfig(
        grpc_port=None
    )
)

BAR_CLASS = {
    "class": "Bar",
    "vectorizer": "none",
    "properties": [
        {"name": "absBar", "dataType": ["int"]},
        {"name": "start", "dataType": ["text"]},
        {"name": "end", "dataType": ["text"]},
        {"name": "segment", "dataType": ["text"]},
        {"name": "chord", "dataType": ["text"]},
    ],
    "vectorIndexConfig": {
        "distance": "cosine",
        "ef": 128
    }
}

def ensure_schema():
    if client.collections.exists("Bar"):
        client.collections.delete("Bar")
    
    client.collections.create_from_dict(BAR_CLASS)

ensure_schema()

class WeaviateVectorStore:
    def upsert(self, musicVec, metadata):
        bar = client.collections.get("Bar")
        bar.data.insert(
            properties={
                "file_id" : metadata["file_id"],
                "bar_index": metadata["bar_index"],
                "parent_label": metadata.get("parent_label", ""),
                "start_time": metadata.get("start_time", ""),
                "end_time": metadata.get("end_time", ""),
                "segment": metadata.get("segment", ""),
                "chord": metadata.get("chord", ""),
            },
            vector=musicVec
        )

    # def query(self, query_vec, top_k=5):
    #     bar = client.collections.get("Bar")
    #     return bar.query.near_vector(
    #         near_vector=query_vec,
    #         limit=top_k,
    #         return_metadata=weaviate.classes.MetadataQuery(distance=True),
    #         return_properties=["absBar", "segment", "chord"]
    #     )