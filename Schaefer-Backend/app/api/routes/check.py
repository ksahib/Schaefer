from fastapi import FastAPI, APIRouter
from typing import List
from app.model.midiModel import Note, Marker  
from pydantic import BaseModel
from app.services.jsontoscore import json_to_music21_score
from app.services.Features import analyze_score_by_markers
from app.db.mongo_client import insert_by_label


router = APIRouter()

class MidiData(BaseModel):
    bpm: int
    notes: List[Note]
    markers: List[Marker]

@router.post("/analyse-midi-json/", tags=["midi"])
async def analyze_midi_json(data: MidiData):
    score = json_to_music21_score(data.notes, data.bpm)
    results = analyze_score_by_markers(score, data.markers, data.bpm)
    print(results)
    insert_by_label("mongodb://localhost:27017/", "featureDB", "songsections", results)



