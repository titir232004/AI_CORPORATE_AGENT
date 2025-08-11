import re
from typing import Optional
MAPPING = {
    "Articles of Association": ["articles of association", "aoa"],
    "Memorandum of Association": ["memorandum of association", "moa"],
    "Board Resolution": ["board resolution", "resolution of the board"],
    "UBO Declaration Form": ["ubo declaration", "ultimate beneficial owner"],
    "Register of Members and Directors": ["register of members", "register of directors"],
    "Shareholder Resolution Templates": ["shareholder resolution","shareholder resolution templates","resolution of shareholders"],
    "Incorporation Application Form":["incorporation application","form for incorporation application"],
    "Change of Registered Address Notice":["change of registered address notice","notice about change of registered address"]
}

def classify_document(text: str) -> str:
    text_l = text.lower()
    for doc_type, patterns in MAPPING.items():
        for p in patterns:
            if p in text_l:
                return doc_type
    return "Unknown"

def best_effort_title(text: str) -> Optional[str]:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return None
