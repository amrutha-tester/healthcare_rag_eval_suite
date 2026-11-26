from pymupdf import open
import re
from typing import List
from pathlib import Path

def extract_paragraphs(pdf_path: str | Path) -> List[str]:
    doc = open(pdf_path)
    raw_blocks: List[str] = []

    for page in doc:
        blocks = sorted(page.get_text("blocks"), key=lambda b: (b[1], b[0]))
        for block in blocks:
            text = re.sub(r"\s+", " ", block[4]).strip()
            if not text or text.lower().startswith("source:"):
                continue
            raw_blocks.append(text)
    doc.close()

    chunks: List[str] = []
    pending_heading: str | None = None

    for i, text in enumerate(raw_blocks):
        # Skip standalone PDF title on line 0
        if i == 0 and len(text) < 110 and not text.endswith("."):
            continue

        # Hold short heading lines and attach them to the next body paragraph
        if len(text) < 110 and not text.endswith("."):
            pending_heading = text
            continue

        combined = f"{pending_heading}: {text}" if pending_heading else text
        pending_heading = None

        if len(combined) >= 60:
            chunks.append(combined)

    return chunks
    
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

