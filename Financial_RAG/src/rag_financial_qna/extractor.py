from bs4 import BeautifulSoup
import os
import re

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".html", ".htm"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        soup = BeautifulSoup(content, "html.parser")

        # Remove scripts, styles, metadata
        for tag in soup.find_all(["script", "style", "head", "link", "meta", "ix:header"]):
            tag.decompose()

        # Remove ixbrl tags but keep the text inside
        for tag in soup.find_all(True):
            if tag.name.startswith("ix:"):
                tag.unwrap()

        text = soup.get_text(separator="\n")
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    elif ext == ".pdf":
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for p in pdf.pages:
                t = p.extract_text()
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts)

    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    else:
        raise ValueError(f"Unsupported file format: {ext}")
