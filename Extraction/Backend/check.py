from fastapi import FastAPI
from typing import List
from midiModel import Note, Marker  
from pydantic import BaseModel
from jsontoscore import json_to_music21_score
from Features import analyze_score_by_markers
app = FastAPI()

class MidiData(BaseModel):
    bpm: int
    notes: List[Note]
    markers: List[Marker]

@app.post("/analyze-midi-json/")
async def analyze_midi_json(data: MidiData):
    score = json_to_music21_score(data.notes, data.bpm)
    results = analyze_score_by_markers(score, data.markers, data.bpm)
    return {"sections": results}
