from pydantic import BaseModel
from typing import List, Optional

class BarLabel(BaseModel):
    label: str
    start_bar: float
    end_bar: float

class IndexedBarLabel(BaseModel):
    segment_id: str
    bar_index: int
    label: Optional[str] = None
    start_bar: Optional[int] = None
    end_bar: Optional[int] = None


class MidiIngestionResponse(BaseModel):
    indexed_bars: List[IndexedBarLabel]