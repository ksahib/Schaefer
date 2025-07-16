from fastapi import APIRouter, Depends, HTTPException
from app.model.schemas import ChatRequest, ChatResponse
from app.services.retrieval import build_prompt

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    docs = build_prompt(request.query)
    return ChatResponse(
        response=docs,
        sources=[docs.metadata['source'] for doc in docs]
    )