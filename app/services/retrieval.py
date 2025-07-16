from transformers import AutoModelForCausalLM, AutoTokenizer
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from app.db.client import semantic_search

model_name = "Qwen/Qwen3-0.6B"
tokeniser = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
_mongo_client = MongoClient("mongodb://localhost:27017/")
_db           = _mongo_client["featureDB"]["songsections"]

llm_model = "Qwen/QwQ-32B"
llm_model = AutoModelForCausalLM.from_pretrained(
    llm_model,
    torch_dtype="auto",
    device_map="auto"
)
llm_tokeniser = AutoTokenizer.from_pretrained(llm_model)

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
    semantic = semantic_search(embed, top_k=5)
    return semantic
    

def build_prompt(query:str):
    section = parse_intent(query)
    relevant_info = retrieve_relevant_info(section)
    features = retrieve_features(section)
    prompt=f"You are a world‑class music theory tutor.  When answering, be precise, reference specific bars or measures, and explain your reasoning in clear, pedagogical language.\n" \
    "=======MUSICAL CONTEXT=======\n" \
    "{features}\n" \
    "=======TEXTUAL CONTEXT=======\n" \
    "{relevant_info}\n" \
    "=======USER QUESTION========\n" \
    "{query}\n" \
    "=======YOUR ANSWER=========\n"
    return prompt

def generate_response(prompt:str):
    messages = [
        {"role": "user", "content": prompt}
    ]
    text = llm_tokeniser.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    model_inputs = llm_tokeniser([text], return_tensors="pt").to(llm_model.device)

    generated_ids = llm_model.generate(
        **model_inputs,
        max_new_tokens=1024
    )

    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = llm_tokeniser.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print(response)




# query = "Why does the hook feel so gloomy?"
# section = parse_intent(query)
# print(f"Section identified: {section}")
# mid_prompt = retrieve_features(section)
# embed = embed_features_query(mid_prompt, query)
# semantic_search_query(embed, top_k=5)


