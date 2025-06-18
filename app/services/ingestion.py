import pretty_midi
import io
from typing import List, Optional
from app.db.client import WeaviateVectorStore
from transformers import AutoTokenizer, AutoModel, BertTokenizer
from app.model.midi_models import BarLabel, IndexedBarLabel
from miditok import REMI, TokenizerConfig
import uuid
import miditoolkit

musicbert = AutoModel.from_pretrained("ruru2701/musicbert-v1.1")

config = TokenizerConfig(
    num_velocities=16,
    use_chords=True,
    use_rests=False,
    use_tempos=True,
    use_time_signatures=True,
    use_programs=False,
    num_tempos=32,
    tempo_range=(40, 250))
tokenizer = REMI(config)

def extract_midi_slice(midi: miditoolkit.MidiFile, start_bar: int, end_bar: int) -> bytes:
    time_signature = midi.time_signature_changes[0] if midi.time_signature_changes else None
    ticks_per_beat = midi.ticks_per_beat
    # beats_per_bar = time_signature.numerator if time_signature else 4  # fallback to 4/4
    beats_per_bar = 4
    ticks_per_bar = ticks_per_beat * beats_per_bar

    start_tick = start_bar * ticks_per_bar
    end_tick   = end_bar * ticks_per_bar

    new_midi = miditoolkit.MidiFile(ticks_per_beat=ticks_per_beat)

    instrument = midi.instruments[0] 
    new_instrument = miditoolkit.Instrument(program=instrument.program, is_drum=instrument.is_drum, name=instrument.name)
    for note in instrument.notes:
        if start_tick <= note.start < end_tick:
            new_note = miditoolkit.Note(
                velocity=note.velocity,
                pitch=note.pitch,
                start=note.start - start_tick,
                end=min(note.end, end_tick) - start_tick
            )
            new_instrument.notes.append(new_note)

    # 7) Only add the instrument if it has notes
    if new_instrument.notes:
        new_midi.instruments.append(new_instrument)

    # 8) Copy any tempo changes inside this bar (shifted)
    for tempo in midi.tempo_changes:
        if start_tick <= tempo.time < end_tick:
            new_midi.tempo_changes.append(
                miditoolkit.TempoChange(
                    tempo=tempo.tempo,
                    time=tempo.time - start_tick
                )
            )

    return new_midi


async def ingest_bars(
        midi_bytes: bytes,
        file_name: str,
        bpm: int,
        parent_label: List[BarLabel],
) -> dict:
    pm = pretty_midi.PrettyMIDI(io.BytesIO(midi_bytes))
    seconds_per_beat = 60 / bpm
    beats_per_bar = pm.time_signature_changes[0].numerator if pm.time_signature_changes else 4
    sec_per_bar      = seconds_per_beat * beats_per_bar
    total_time       = pm.get_end_time()
    num_bars         = int(total_time / sec_per_bar) + 1

    bars = []

    for i in range(num_bars):
        start = i * sec_per_bar
        end   = min((i+1) * sec_per_bar, total_time)
        # find any matching parent label
        pl = next(
          (lbl.label for lbl in parent_label
             if lbl.start_bar <= i <= lbl.end_bar),
          None
        )
        bars.append({"bar_index": i, "start": start, "end": end, "parent_label": pl})

    file_id = str(uuid.uuid4())
    indexed = []
    for bar in bars:
        remi = REMI()
        midi = miditoolkit.MidiFile(io.BytesIO(midi_bytes))
        midi_bar = extract_midi_slice(midi, bar["start"], bar["end"])
        tokens = remi(midi_bar)

        token_strs = [str(tok) for tok in tokens.tokens]
        encoded = tokenizer(token_strs, return_tensors="pt", padding=True, truncation=True)

        output = musicbert(**encoded)
        embedding = output.last_hidden_state.mean(dim=1)

        seg_id    = f"{file_id}#bar{bar['bar_index']}"

        meta = {
          "file_id":      file_id,
          "bar_index":    bar["bar_index"],
          "parent_label": bar["parent_label"],
          "start_time":   bar["start"],
          "end_time":     bar["end"],
          "filename":     file_name
        }
        WeaviateVectorStore.upsert([(seg_id, embedding, meta)])
        indexed.append(IndexedBarLabel(
            segment_id=seg_id,
            bar_index=bar["bar_index"],
            parent_label=bar["parent_label"],
        ))

    return {"file_id": file_id, "indexed_bars": indexed}