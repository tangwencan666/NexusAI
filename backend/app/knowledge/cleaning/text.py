import re


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    cleaned: list[str] = []
    previous = None
    blanks = 0
    for line in lines:
        if not line:
            blanks += 1
            if blanks <= 1 and cleaned:
                cleaned.append("")
            continue
        blanks = 0
        if line == previous:
            continue
        cleaned.append(line)
        previous = line
    return "\n".join(cleaned).strip()
