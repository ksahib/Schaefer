from sentence_transformers import SentenceTransformer
from client import WeaviateVectorStore
from chunking import split_into_paragraph,group_paragraph
import os
import weaviate
import client


embedder = SentenceTransformer("all-MiniLM-L6-v2")
vector_store = WeaviateVectorStore(client)

def process_theory_text_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    
    paragraphs = split_into_paragraph(text)
    chunks = group_paragraph(paragraphs)

    vectors = embedder.encode(chunks)

    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        vector_store.upsert(
            embedding=vec,
            metadata={
                "chunk_text": chunk,
                "source": os.path.basename(filepath),
                "chunk_index": i
            }
        )


for file in os.listdir("omt_texts"):
    if file.endswith(".txt"):
        process_theory_text_file(os.path.join("omt_texts", file))
