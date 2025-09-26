import os, re, json

def word_count(text: str) -> int:
    return len(text.split())

def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()
