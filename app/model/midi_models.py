from pydantic import BaseModel
from typing import List, Optional

class BarLabel(BaseModel):
    label: str
    start_bar: float
    end_bar: float

class IndexedBarLabel(BarLabel):
    segment_id: str
    bar_index: int
    parent_label: Optional[str]

class MidiIngestionResponse(BaseModel):
    indexed_bars: List[IndexedBarLabel]