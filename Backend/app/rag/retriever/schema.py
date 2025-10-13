from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Document:
    text: str
    metadata: Dict[str, Any]