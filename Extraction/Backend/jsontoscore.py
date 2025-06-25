from music21 import stream, note, tempo, meter
from typing import List
from midiModel import Note

def json_to_music21_score(notes: List[Note], bpm: int) -> stream.Score:
    s = stream.Score()
    p = stream.Part()

    
    ts = meter.TimeSignature('4/4')  
    mm = tempo.MetronomeMark(number=bpm)
    p.insert(0, ts)
    p.insert(0, mm)

    # Add notes
    for n in notes:
        new_note = note.Note(n.pitch)
        new_note.quarterLength = n.duration
        new_note.offset = n.start  
        p.insert(new_note.offset, new_note)

    s.insert(0, p)

   
    s = s.makeMeasures()

    return s
