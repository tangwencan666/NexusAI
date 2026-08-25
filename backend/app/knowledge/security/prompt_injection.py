import re

PATTERNS = [
    r"ignore (all |the )?(previous|prior) instructions",
    r"system prompt",
    r"developer message",
    r"reveal (the )?(secret|api key|password)",
    r"execute (this |the )?(command|shell)",
]


def prompt_injection_risk(content: str) -> dict[str, object]:
    matches = [pattern for pattern in PATTERNS if re.search(pattern, content, re.IGNORECASE)]
    return {"prompt_injection_risk": bool(matches), "prompt_injection_signals": matches}
