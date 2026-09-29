"""The one seam where real data plugs in. Graph and verifiers only ever see a Corpus."""
from abc import ABC, abstractmethod
from models import Corpus

class DocumentSource(ABC):
    @abstractmethod
    def load(self) -> Corpus:
        """Return contracts, specs and drawing metadata normalized into a Corpus."""
