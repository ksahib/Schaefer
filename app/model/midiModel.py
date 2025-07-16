from pydantic import BaseModel
from typing import List

class Note(BaseModel):
    pitch: int
    start: float  
    duration: float

class Marker(BaseModel):
    label: str
    start_bar: int
    end_bar: int

class MidiData(BaseModel):
    bpm: int
    notes: List[Note]
    markers: List[Marker]