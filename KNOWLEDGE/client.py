import weaviate
import weaviate.classes as wvc
from sentence_transformers import SentenceTransformer
import os
import time

weaviate_client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=wvc.init.AdditionalConfig(grpc_port=50051)
)


MUSIC_THEORY_DOCUMENT_CLASS = {
    "class": "MusicTheory",
    "vectorizer": "none",
    "properties": [
        {"name": "chunk", "dataType": ["text"]},
        {"name": "source", "dataType": ["text"]},
        {"name": "chunk_index", "dataType": ["int"]}
    ],
    "vectorIndexConfig": {
        "distance": "cosine",
        "ef": 128
    }
}

def ensure_schema():
    if weaviate_client.collections.exists("MusicTheory"):
        weaviate_client.collections.delete("MusicTheory")
    weaviate_client.collections.create_from_dict(MUSIC_THEORY_DOCUMENT_CLASS)

class WeaviateVectorStore:
    def __init__(self, client):
        self.collection = client.collections.get("MusicTheory")

    def upsert(self, embedding, metadata):
       
        vector = embedding.tolist() if hasattr(embedding, "tolist") else embedding
        self.collection.data.insert(
            properties={
                "chunk": metadata["chunk_text"],
                "source": metadata["source"],
                "chunk_index": int(metadata["chunk_index"]) 
            },
            vector=vector
        )
        time.sleep(0.1)

# Chunking functions
def split_into_paragraph(text):
    """More robust paragraph splitting"""
    # First normalize all line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Split on double newlines or large indents
    paragraphs = []
    current_para = []
    
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:  # Empty line indicates paragraph break
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
        elif line.startswith(('    ', '\t')):  # Indented line
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
            current_para.append(stripped)
        else:
            current_para.append(stripped)
    
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    return [p for p in paragraphs if p]

def group_paragraph(paragraphs, max_chars=800):
    """More conservative chunking"""
    chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para_length = len(para)
        
        # Always start new chunk if current would become too large
        if current_length + para_length > max_chars:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            # If single paragraph is too long, split it
            if para_length > max_chars:
                words = para.split()
                temp_para = []
                temp_length = 0
                
                for word in words:
                    if temp_length + len(word) > max_chars:
                        chunks.append(' '.join(temp_para))
                        temp_para = []
                        temp_length = 0
                    temp_para.append(word)
                    temp_length += len(word) + 1  # +1 for space
                
                if temp_para:
                    chunks.append(' '.join(temp_para))
                continue
        
        current_chunk.append(para)
        current_length += para_length + 1  # +1 for space
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def process_theory_text_file(filepath, vector_store, embedder):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"\nProcessing: {os.path.basename(filepath)}")
    paragraphs = split_into_paragraph(text)
    print(f"Found {len(paragraphs)} paragraphs")
    
    chunks = group_paragraph(paragraphs)
    print(f"Created {len(chunks)} chunks")
    
    # Skip files that are too small (optional)
    if len(chunks) == 1 and len(chunks[0]) < 500:
        print("Skipping - content too short")
        return
    
    vectors = embedder.encode(chunks)
    
    for chunk_index, (chunk, vec) in enumerate(zip(chunks, vectors)):
        print(f"  Chunk {chunk_index}: {len(chunk)} chars")
        vector_store.upsert(
            embedding=vec,
            metadata={
                "chunk_text": chunk,
                "source": os.path.basename(filepath),
                "chunk_index": chunk_index
            }
        )

def reset_collection():
    if weaviate_client.collections.exists("MusicTheory"):
        weaviate_client.collections.delete("MusicTheory")
    weaviate_client.collections.create_from_dict(MUSIC_THEORY_DOCUMENT_CLASS)

if __name__ == "__main__":
    # Initialize components
    reset_collection()
    time.sleep(0.1)
    ensure_schema()
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    vector_store = WeaviateVectorStore(weaviate_client)
    
    # Process files
    text_dir = "omt_texts"
    for file in os.listdir(text_dir):
        if file.endswith(".txt"):
            print(f"Processing {file}...")
            process_theory_text_file(
                os.path.join(text_dir, file),
                vector_store,
                embedder
            )
    
    print("Ingestion complete!")
    weaviate_client.close()
    