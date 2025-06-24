from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import json
from app.model.midi_models import MidiIngestionResponse, BarLabel
from app.services.ingestion import ingest_bars


router = APIRouter()

@router.post("/upload", response_model=MidiIngestionResponse,  tags=["midi"])
async def upload_midi(
    file:UploadFile = File(...),
    bpm: int = Form(...),
    labels_json: Optional[str] = Form(None)
):
    if bpm <= 0:
        raise HTTPException(400, "BPM must be a positive integer")
    
    parent_label = []
    if labels_json:
        try:
            parent_label = [BarLabel(**lbl) for lbl in json.loads(labels_json)]
        except Exception as e:
            raise HTTPException(400, f"Invalid labels_json: {e}")
    data = await file.read()
    result = await ingest_bars(
        midi_bytes=data,
        file_name=file.filename,
        bpm=bpm,
        parent_label=parent_label,
    )
    return result