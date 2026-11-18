import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.vectorstores import InMemoryVectorStore

# Ensure the project root is in Python's path, then import from RAG1.file_reader
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from RAG1.file_reader import extract_paragraphs_from_folder

load_dotenv()

# 1. Choose the free embedding model (Ollama locally by default, or Gemini in CI)
provider = os.getenv("LLM_PROVIDER", "ollama").lower()

if provider == "gemini":
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    embedding = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
else:
    from langchain_ollama import OllamaEmbeddings

    embedding = OllamaEmbeddings(model="nomic-embed-text")

# 2. Initialize the in-memory vector store
vector_store = InMemoryVectorStore(embedding)
vectore_store = vector_store  # Alias in case later video files use the author's spelling

# 3. Extract paragraphs from all 10 healthcare PDFs in data/leaflets/
LEAFLETS_DIR = Path(__file__).resolve().parent.parent / "data" / "leaflets"
chunks = extract_paragraphs_from_folder(LEAFLETS_DIR)

# 4. Embed and store all chunks in the vector store
vector_store.add_texts(texts=chunks)
print(f"Indexed {len(chunks)} chunks from {LEAFLETS_DIR.name}/ using {provider} embeddings")

