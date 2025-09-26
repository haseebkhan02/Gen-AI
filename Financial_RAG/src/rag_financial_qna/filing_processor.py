import os
import glob
from .extractor import extract_text
from .chunker import chunk_text
from .utils import save_json

def process_filings(input_dir, output_dir):
    files = glob.glob(os.path.join(input_dir, '*'))
    os.makedirs(output_dir, exist_ok=True)
    
    processed_count = 0
    
    for f in files:
        try:
            text = extract_text(f)

            if not isinstance(text, str):
                raise TypeError(f"extract_text did not return string for {f}")

            chunks = chunk_text(text, chunk_size=200, overlap=50)

            # Ensure every chunk is JSON serializable
            chunks_dict = [{"text": str(c)} for c in chunks]

            base = os.path.basename(f)
            save_json(os.path.join(output_dir, f"{base}.json"), chunks_dict)
            processed_count += 1

        except Exception as e:
            print(f"[ERROR] Failed to process {f}: {e}")
    
    print(f"Processed {processed_count} filings into {output_dir}")
