from music21 import stream, meter, key, chord
from typing import List
from app.model.midiModel import Marker
def extract_music21_features(section_stream: stream.Stream) -> dict:
    features = {}

    # Key and mode
    try:
        k = section_stream.analyze('key')
        features['key'] = k.tonic.name
        features['mode'] = k.mode
        features['scale'] = [p.name for p in k.getScale().getPitches()]
    except Exception:
        features['key'] = 'unknown'
        features['mode'] = 'unknown'
        features['scale'] = []

    # Time signature
    try:
        ts = section_stream.recurse().getElementsByClass(meter.TimeSignature)[0]
        features['time_signature'] = str(ts.ratioString)
    except IndexError:
        features['time_signature'] = '4/4'

    # Chords info
    chords_info = []
    chords = section_stream.chordify().recurse().getElementsByClass('Chord')
    for c in chords:
        if not c.isRest:
            chords_info.append({
                'chord': c.pitchedCommonName,
                'root': c.root().name if c.root() else None,
                'inversion': c.inversion(),
                'is_consonant': c.isConsonant()
            })
    features['chords'] = chords_info

    return features
def analyze_score_by_markers(score: stream.Score, markers: List[Marker], bpm: int):
    beats_per_bar = 4
    seconds_per_beat = 60 / bpm
    results = []

    for marker in markers:
        # music21 measures start from 1
        section = score.measures(marker.start_bar + 1, marker.end_bar + 1)

        features = extract_music21_features(section)

        start_time = marker.start_bar * beats_per_bar * seconds_per_beat
        end_time = (marker.end_bar + 1) * beats_per_bar * seconds_per_beat

        results.append({
            "label": marker.label,
            "start_bar": marker.start_bar,
            "end_bar": marker.end_bar,
            "start_time": start_time,
            "end_time": end_time,
            "features": features
        })

    return results
