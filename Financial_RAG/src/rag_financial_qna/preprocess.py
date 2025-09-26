import pdfplumber
from .utils import clean_text, word_count

def extract_text(path: str) -> str:
    path = path.lower()
    if path.endswith('.pdf'):
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                t = p.extract_text()
                if t:
                    text_parts.append(t)
        return '\n'.join(text_parts)
    else:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

def chunk_text(text: str, target_words=250, overlap=50):
    paras = [clean_text(p) for p in text.split('\n') if p.strip()]
    chunks, cur, cur_words = [], [], 0

    for p in paras:
        wc = word_count(p)
        if cur_words + wc > target_words and cur:
            chunks.append(' '.join(cur))
            # handle overlap safely
            if overlap > 0 and len(cur) >= overlap:
                cur = cur[-overlap:]
                cur_words = sum(word_count(x) for x in cur)
            else:
                cur = []
                cur_words = 0
        cur.append(p)
        cur_words += wc

    if cur:
        chunks.append(' '.join(cur))

    # wrap chunks into dicts for consistency
    return [{'text': c} for c in chunks]
