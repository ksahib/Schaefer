import weaviate

# Initialize client with the new connection method
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=weaviate.classes.init.AdditionalConfig(
        grpc_port=None  # Proper way to disable gRPC
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

# Call at import or in app-startup hook
ensure_schema()

class WeaviateVectorStore:
    def upsert(self, musicVec, metadata):
        bar = client.collections.get("Bar")
        bar.data.insert(
            properties={
                "absBar": metadata["absBar"],
                "start": metadata.get("start", ""),
                "end": metadata.get("end", ""),
                "segment": metadata.get("segment", ""),
                "chord": metadata.get("chord", ""),
            },
            vector=musicVec
        )

    # Example query method (uncomment if needed)
    # def query(self, query_vec, top_k=5):
    #     bar = client.collections.get("Bar")
    #     return bar.query.near_vector(
    #         near_vector=query_vec,
    #         limit=top_k,
    #         return_metadata=weaviate.classes.MetadataQuery(distance=True),
    #         return_properties=["absBar", "segment", "chord"]
    #     )