import os
from .filing_processor import process_filings
from .extractor import extract_text as extract_text_from_file  # reuse extractor

def extract_text(input_dir):
    """Extract text from all files in input_dir and return as a list of strings"""
    docs = []
    for file_name in os.listdir(input_dir):
        path = os.path.join(input_dir, file_name)
        try:
            text = extract_text_from_file(path)
            if text.strip():  # skip empty files
                docs.append(text)
        except Exception as e:
            print(f"[WARN] Failed to extract text from {path}: {e}")
    return docs

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    args = parser.parse_args()
    process_filings(args.input_dir, args.output_dir)
