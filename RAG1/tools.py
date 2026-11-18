import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from RAG1.indexing import vector_store
from langchain_core.tools import tool

last_retrieved_context: List[str] = []


@tool(response_format="content_and_artifact")
def collecting_info(query: str) -> Tuple[str, List[str]]:
    """
    Search the healthcare PDF leaflets knowledge base and return relevant information for the user's question.
    """
    global last_retrieved_context
    docs = vector_store.similarity_search(query, k=4)

    chunks = [doc.page_content for doc in docs]
    last_retrieved_context = chunks

    # Returns (text_for_llm, raw_chunks_list_for_deepeval)
    return "\n\n".join(chunks), chunks
