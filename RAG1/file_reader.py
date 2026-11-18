from pymupdf import open
import re
from typing import List
from pathlib import Path

def extract_paragraphs(pdf_path: str | Path) -> List[str]:
    # This function takes a pdf path and return an array of paragraphs
    doc = open(pdf_path)
    paragraphs = []
    for page in doc:
        # 1. Get all text blocks on the current page
        blocks = page.get_text("blocks")
        # 2. Sort blocks from top-to-bottom (y0), then left-to-right (x0)
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
        # 3. Clean each block and add to our list
        for block in blocks:
            text = block[4]
            # Replace line breaks / multiple spaces inside a paragraph with a single space
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                paragraphs.append(text)
    doc.close()
    return paragraphs
    
def extract_paragraphs_from_folder(folder_path: str | Path) -> List[str]:
    """Extract paragraphs from ALL PDF files inside a folder (e.g. data/leaflets)."""
    folder = Path(folder_path)
    all_paragraphs = []
    # Loop through all .pdf files in alphabetical order (01_..., 02_..., etc.)
    for pdf_file in sorted(folder.glob("*.pdf")):
        file_paragraphs = extract_paragraphs(pdf_file)
        # Prefix each paragraph with the leaflet name so the LLM knows which drug/topic it belongs to
        for para in file_paragraphs:
            all_paragraphs.append(f"[{pdf_file.stem}] {para}")
    return all_paragraphs

if __name__ == "__main__":
    chunks = extract_paragraphs_from_folder("data/leaflets")
    print(f"Total paragraphs extracted across all 10 PDFs: {len(chunks)}")
    print("Sample paragraph 1:", chunks[0])
    print("Sample paragraph 2:", chunks[1])

