from transformers import AutoModelForCausalLM, AutoTokenizer
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from app.db.client import semantic_search
from llama_cpp import Llama

model_name = "Qwen/Qwen3-0.6B"
tokeniser = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
_mongo_client = MongoClient("mongodb://localhost:27017/")
_db           = _mongo_client["featureDB"]["songsections"]


# llm_model = CAM.from_pretrained(
#     "/home/kazisahib/schaefer-backend/app/LLM/capybarahermes-2.5-mistral-7b.Q4_K_M.gguf",
#     model_type="qwen1.5",
#     max_new_tokens=5000,
#     temperature=0.7,
#     top_p=0.9,
#     repetition_penalty=1.1
# )

llm_model = Llama(
    model_path="C:/project/Schaefer/app/LLM/capybarahermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=2010,
    n_gpu_layers=20,
)

#llm_tokeniser = AutoTokenizer.from_pretrained(llm_model_name)

def parse_intent(query: str) -> str:
    sections = _db.distinct("sections")
    if not sections:
        sections = ['none']
    prompt = (
        "You are an intent parser.  Given a single query, you MUST respond with exactly one "
        "of these sections (or 'none'): "
        + ", ".join(sections)
        + ".\n\n"
        f"Query: {query}\n"
        "Section:"
    )
    print(prompt)
    inputs = tokeniser(prompt, return_tensors="pt").to(model.device)
    prompt_len = inputs["input_ids"].shape[-1]

    out = model.generate(
        **inputs,
        max_new_tokens=5,      
        do_sample=False,
        num_beams=1,
        eos_token_id=tokeniser.eos_token_id,
        pad_token_id=tokeniser.eos_token_id
    )

    new_tokens = out[0, prompt_len:]
    return tokeniser.decode(new_tokens, skip_special_tokens=True).splitlines()[0].strip()



def retrieve_features(section:str):
    results = _db.distinct(section)
    print(list(results))
    return results

def embed_features_query(features: list[dict], query: str):
    feature_texts = []
    for feat in features:
        parts = []
        for k, v in feat.items():
            if isinstance(v, list):
                parts.append(f"{k}: {','.join(map(str, v))}")
            else:
                parts.append(f"{k}: {v}")
        feature_texts.append("; ".join(parts))

    features_str = " | ".join(feature_texts)
    prompt = f"Features for section: {features_str}\nquery: {query}"

    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode(prompt)
    vector = query_embedding.tolist()
    return vector


def retrieve_relevant_info(query:str, section):
    mid_prompt = retrieve_features(section)
    embed = embed_features_query(mid_prompt, query)
    semantic = semantic_search(embed, top_k=1)
    return semantic
    

def build_prompt(query: str):
    section = "Outro"
    relevant_info = retrieve_relevant_info(query, section)
    features      = retrieve_features(section)
    prompt = (
        f"You are a world‑class music theory tutor.  When answering, be precise, "
        f"reference specific bars or measures, and explain your reasoning in clear, "
        f"pedagogical language.\n"
        f"=======MUSICAL CONTEXT=======\n"
        f"{features}\n"
        f"=======TEXTUAL CONTEXT=======\n"
        f"{relevant_info}\n"
        f"=======USER QUESTION========\n"
        f"{query}\n"
        f"=======YOUR ANSWER=========\n"
    )
    return prompt


def generate_response(prompt):
    response = llm_model(
        prompt,
        max_tokens=512,
        echo=False,
    )
    text = response["choices"][0]["text"]
    text = text.strip()
    print(text)
    return text
 




# query = "Why does the hook feel so gloomy?"
# section = parse_intent(query)
# print(f"Section identified: {section}")
# mid_prompt = retrieve_features(section)
# embed = embed_features_query(mid_prompt, query)
# semantic_search(embed, top_k=5)
