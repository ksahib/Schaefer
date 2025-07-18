from transformers import AutoModelForCausalLM as AM, AutoTokenizer
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer, util
from ctransformers import AutoModelForCausalLM as CAM
import torch

# -------- Load models once -------- #
# Intent model
intent_model_name = "distilgpt2"
tokenizer_intent = AutoTokenizer.from_pretrained(intent_model_name)
intent_model = AM.from_pretrained(intent_model_name)

# Sentence embedding model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")


# llm_model_name = "unsloth/Qwen2.5-3B-Instruct-bnb-4bit"
# llm_tokenizer = AutoTokenizer.from_pretrained(llm_model_name)
llm_model = CAM.from_pretrained(
    "E:/PIANO/NEWSCHAEFER/Schaefer/app/GGUF",
    model_file="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    model_type="llama",
    max_new_tokens=512,
    temperature=0.7,
    top_p=0.9,
    repetition_penalty=1.1
)

# -------- MongoDB Connection -------- #
_mongo_client = MongoClient("mongodb://localhost:27017/")
_db = _mongo_client["featureDB"]["songsections"]

# -------- INTENT PARSING -------- #
def parse_intent(query: str) -> str:
    sections = _db.distinct("sections") or ['none']
    prompt = ("You are an intent parser. Given a single query, respond with one section "
              f"from the following (or 'none'): {', '.join(sections)}\nQuery: {query}\nSection:")
    inputs = tokenizer_intent(prompt, return_tensors="pt").to(intent_model.device)
    out = intent_model.generate(
        **inputs, max_new_tokens=5, do_sample=False, num_beams=1,
        eos_token_id=tokenizer_intent.eos_token_id,
        pad_token_id=tokenizer_intent.eos_token_id
    )
    decoded = tokenizer_intent.decode(out[0, inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    return decoded.strip()

# -------- FEATURE RETRIEVAL & EMBEDDING -------- #
def retrieve_features(section):
    return _db.distinct(section)

def embed_features_query(features, query):
    texts = ["; ".join(f"{k}: {', '.join(v) if isinstance(v, list) else v}" for k, v in feat.items())
             for feat in features]
    prompt = f"Features for section: {' | '.join(texts[:20])}\nquery: {query}"
    return embed_model.encode(prompt, convert_to_tensor=True)

def retrieve_relevant_info(query, section):
    features = retrieve_features(section)
    if not features:
        return "No relevant features found."
    query_embed = embed_features_query(features, query)
    corpus_texts = ["; ".join(f"{k}: {', '.join(v) if isinstance(v, list) else v}"
                    for k, v in feat.items()) for feat in features]
    corpus_embeds = embed_model.encode(corpus_texts, convert_to_tensor=True)
    hits = util.semantic_search(query_embed, corpus_embeds, top_k=5)[0]
    return "\n".join(corpus_texts[hit['corpus_id']] for hit in hits)

# -------- BUILD PROMPT -------- #
def build_prompt(query):
    section = parse_intent(query)
    relevant = retrieve_relevant_info(query, section)
    features = retrieve_features(section)[:5]
    return (
        "You are a world-class music theory tutor. Be precise, reference bars, explain clearly.\n"
        f"=======MUSICAL CONTEXT=======\n{features}\n"
        f"=======TEXTUAL CONTEXT=======\n{relevant}\n"
        f"=======USER QUESTION=======\n{query}\n"
        "=======YOUR ANSWER=========\n"
    )

# -------- GENERATE RESPONSE -------- #
def generate_response(prompt):
    response = llm_model(prompt)
    print(response.strip())
    return response.strip()

# -------- Main -------- #
if __name__ == "__main__":
    q = "Why does the piece modulate from A minor to C major in the middle?"
    p = build_prompt(q)
    generate_response(p)
