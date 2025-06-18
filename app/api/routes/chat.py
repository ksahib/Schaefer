from fastapi import APIRouter, Depends, HTTPException
from app.model.schemas import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    docs = await retrieve_documents(request.query)
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found")
    response = await generate_response(request.query, docs)
    if not response:
        raise HTTPException(status_code=500, detail="Failed to generate response")
    return ChatResponse(response=response, sources=[doc.metadata['source'] for doc in docs])