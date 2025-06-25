from sentence_transformers import SentenceTransformer
import re

def split_into_paragraph(text):
    raw_paragraph=re.split(r'\n\s*\n',text)
    return [p.strip() for p in raw_paragraph if p.strip()]

def group_paragraph(paragraphs,max_chars=800):
    chunks=[]
    current_chunk=""

    for para in paragraphs:
        if len(current_chunk)+len(para)>max_chars:
            current_chunk+=para+ "\n\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk= para+"\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    
    return chunks

