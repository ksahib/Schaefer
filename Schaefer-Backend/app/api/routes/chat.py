from fastapi import APIRouter, Depends, HTTPException
from app.model.schemas import ChatRequest, ChatResponse
from app.services.retrieval import build_prompt, generate_response

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    prompt = build_prompt(request.query)
    print(prompt)
    docs = generate_response(prompt)
    return ChatResponse(
        response=docs,
        sources=[]
    )