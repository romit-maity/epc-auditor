"""DocumentSource implementation over the synthetic JSON corpus."""
import json
from pathlib import Path
from models import Corpus
from ingestion.source_interface import DocumentSource
from ingestion.drawing_extraction import extract_callouts

class SyntheticSource(DocumentSource):
    def __init__(self, path: str = str(Path(__file__).parent.parent / "corpus" / "corpus.json")):
        self.path = path

    def load(self) -> Corpus:
        raw = json.loads(Path(self.path).read_text())
        raw["callouts"] = extract_callouts(raw["callouts"])   # the stubbed step
        return Corpus(**raw)
