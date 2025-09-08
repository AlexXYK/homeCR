import re, pathlib

p = pathlib.Path("app.py")
s = p.read_text()

cleanup_block = r'''
DOT_LINE = re.compile(r'^\s*[\.\*·\s]{3,}$')
MULTI_PUNCT = re.compile(r'([.,;:!?])\1{1,}')
MULTI_SPACE = re.compile(r'[ \t]{2,}')
SPACE_BEFORE_PUNCT = re.compile(r'\s+([.,;:!?])')

WHITELIST_KEEP = {"x", "x.", "X", "X.", "note", "Note", "NOTE"}

def _is_mostly_punct(line: str, thresh: float = 0.6) -> bool:
    if not line.strip():
        return True
    total = len(line)
    punct = sum(ch in ".,;:!?*|-_" for ch in line)
    return (punct / total) >= thresh

def _is_noise_short(line: str) -> bool:
    alnum = sum(ch.isalnum() for ch in line)
    if line.strip() in WHITELIST_KEEP:
        return False
    return alnum < 2  # e.g., ".", "*" treated as noise

def clean_text(t: str, drop_dot_lines: bool = True) -> str:
    lines = t.splitlines()
    out = []
    for ln in lines:
        if drop_dot_lines and (DOT_LINE.match(ln) or _is_mostly_punct(ln)):
            continue
        if _is_noise_short(ln):
            continue
        ln = MULTI_PUNCT.sub(r'\1', ln)
        ln = SPACE_BEFORE_PUNCT.sub(r'\1', ln)
        ln = MULTI_SPACE.sub(' ', ln)
        ln = ln.strip()
        out.append(ln)
    out = [l for l in out if l]
    s = "\n".join(out)
    s = re.sub(r'\n{3,}', '\n\n', s).strip()
    return s
'''

# Replace old cleanup function
s = re.sub(r'DOT_LINE.*?def clean_text\([^\)]*\):.*?return s',
           cleanup_block.strip().replace('\\','\\\\').replace('\n','\\n'),
           s, flags=re.S)

p.write_text(s)
print("Patched cleanup in app.py (ASCII-safe)")

