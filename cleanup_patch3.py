import re, pathlib

p = pathlib.Path("app.py")
s = p.read_text()

cleanup_block = r'''
import unicodedata

MULTI_PUNCT = re.compile(r'([.,;:!?])\1{1,}')
MULTI_SPACE = re.compile(r'[ \t]{2,}')
SPACE_BEFORE_PUNCT = re.compile(r'\s+([.,;:!?])')

WHITELIST_KEEP = {"x", "x.", "X", "X.", "note", "Note", "NOTE"}

def _ratio_non_alnum(line: str) -> float:
    if not line:
        return 1.0
    total = len(line)
    non_alnum = sum(0 if (ch.isalnum() or ch.isspace()) else 1 for ch in line)
    return non_alnum / max(total, 1)

def _is_mostly_punct_or_symbols(line: str, thresh: float = 0.55) -> bool:
    """Drop lines with lots of bullets/dots/symbols (unicode-safe)."""
    if not line.strip():
        return True
    return _ratio_non_alnum(line) >= thresh

def _is_numbery(line: str, thresh_digits: float = 0.6) -> bool:
    """Drop lines that are mostly digits (e.g., '18', '74.')."""
    s = line.strip()
    if not s:
        return True
    digits = sum(ch.isdigit() for ch in s)
    return (digits / len(s)) >= thresh_digits

def _few_letters(line: str, min_letters: int = 2) -> bool:
    """Drop lines with very few letters unless explicitly whitelisted."""
    if line.strip() in WHITELIST_KEEP:
        return False
    letters = sum(ch.isalpha() for ch in line)
    return letters < min_letters

def clean_text(t: str, drop_dot_lines: bool = True) -> str:
    lines = t.splitlines()
    out = []
    for ln in lines:
        # Hard filters
        if _is_mostly_punct_or_symbols(ln):
            continue
        if _is_numbery(ln):
            continue
        if _few_letters(ln):
            continue
        # Light normalization
        ln = MULTI_PUNCT.sub(r'\1', ln)
        ln = SPACE_BEFORE_PUNCT.sub(r'\1', ln)
        ln = MULTI_SPACE.sub(' ', ln).strip()
        if ln:
            out.append(ln)
    # Collapse excess blanks
    text = "\n".join(out)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text
'''

# Replace the old cleanup (from the previous DOT_LINE... block up to 'return s')
s = re.sub(
    r'MULTI_PUNCT.*?def clean_text\([^\)]*\):.*?return s',
    cleanup_block.strip().replace('\\','\\\\').replace('\n','\\n'),
    s,
    flags=re.S
)

p.write_text(s)
print("Patched cleanup in app.py (unicode-aware)")

