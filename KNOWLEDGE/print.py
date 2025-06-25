import weaviate

client = weaviate.Client("http://localhost:8080")

result = client.query.get(
    "MusicTheory",
    ["chunk", "source", "chunk_index"]
).with_limit(5).do()

for obj in result['data']['Get']['MusicTheory']:
    print(f"Chunk #{obj['chunk_index']} from {obj['source']}:")
    print(obj['chunk'][:200], '...\n')
