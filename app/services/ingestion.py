import tempfile
import pretty_midi
import io
import symusic
from typing import List, Optional
from app.db.client import WeaviateVectorStore
from transformers import AutoTokenizer, AutoModel, BertTokenizer
from app.model.midi_models import BarLabel, IndexedBarLabel
from miditok import REMI, TokenizerConfig
import uuid
import miditoolkit
import torch

musicbert = AutoModel.from_pretrained("ruru2701/musicbert-v1.1")

remi_config = TokenizerConfig(
    num_velocities=16,
    use_chords=True,
    use_rests=False,
    use_tempos=True,
    use_time_signatures=True,
    use_programs=False,
    num_tempos=32,
    tempo_range=(40, 250)
)
remi_tokenizer = REMI(remi_config)

def extract_midi_slice(midi: miditoolkit.MidiFile, start_bar: int, end_bar: int) -> bytes:
    time_signature = midi.time_signature_changes[0] if midi.time_signature_changes else None
    ticks_per_beat = midi.ticks_per_beat
    # beats_per_bar = time_signature.numerator if time_signature else 4  
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

    if new_instrument.notes:
        new_midi.instruments.append(new_instrument)

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
    sec_per_bar = seconds_per_beat * beats_per_bar
    total_time = pm.get_end_time()
    num_bars = int(total_time / sec_per_bar) + 1

    bars = []
    for i in range(num_bars):
        start = i * sec_per_bar
        end = min((i + 1) * sec_per_bar, total_time)
        pl = next(
            (lbl.label for lbl in parent_label if lbl.start_bar <= i <= lbl.end_bar),
            None
        )
        bars.append({"bar_index": i, "start": start, "end": end, "parent_label": pl})

    file_id = str(uuid.uuid4())
    indexed = []

    with tempfile.NamedTemporaryFile(suffix='.mid') as temp_file:
        temp_file.write(midi_bytes)
        temp_file.flush()

        score = symusic.Score(temp_file.name)

        for bar in bars:
            ticks_per_beat = score.ticks_per_quarter
            ticks_per_bar = ticks_per_beat * beats_per_bar
            start_tick = int(bar["bar_index"] * ticks_per_bar)
            end_tick = int((bar["bar_index"] + 1) * ticks_per_bar)

            bar_score = score.clip(start_tick, end_tick)

            remi_tokens = remi_tokenizer.encode(bar_score)
            token_strs = [str(tok) for tok in remi_tokens]

            unique_tokens = list(set(token_strs))
            token_to_id = {tok: idx + 1 for idx, tok in enumerate(unique_tokens)}  # Padding at 0
            token_ids = [token_to_id[tok] for tok in token_strs]

            max_length = 512
            token_ids_padded = token_ids[:max_length] + [0] * (max_length - len(token_ids[:max_length]))
            input_tensor = torch.tensor([token_ids_padded], dtype=torch.long)
            attention_mask = (input_tensor != 0).long()

            output = musicbert(input_ids=input_tensor, attention_mask=attention_mask)
            embedding = output.last_hidden_state.mean(dim=1)

            seg_id = f"{file_id}#bar{bar['bar_index']}"

            meta = {
                "file_id": file_id,
                "bar_index": bar["bar_index"],
                "parent_label": bar["parent_label"],
                "start_time": bar["start"],
                "end_time": bar["end"],
                "filename": file_name
            }
            WeaviateVectorStore.upsert(seg_id, embedding, meta)
            indexed.append(IndexedBarLabel(
                segment_id=seg_id,
                bar_index=bar["bar_index"],
                parent_label=bar["parent_label"],
            ))

    return {"file_id": file_id, "indexed_bars": indexed}