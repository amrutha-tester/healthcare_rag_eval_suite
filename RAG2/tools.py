import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from RAG2.indexing import vector_store
from langchain_core.tools import tool

last_retrieved_context: List[str] = []

# TOP_K = 2
# MIN_SECOND_SCORE = 0.55
# MAX_SCORE_GAP = 0.12

@tool(response_format="content_and_artifact")
def collecting_info(query: str) -> Tuple[str, List[str]]:
    """
    Search the healthcare PDF leaflets knowledge base and return the single most relevant chunk.
    """
    global last_retrieved_context
    docs = vector_store.similarity_search(query, k=1)

    chunks = [doc.page_content for doc in docs]
    last_retrieved_context = chunks
    return "\n\n".join(chunks), chunks

# @tool(response_format="content_and_artifact")
# def collecting_info(query: str) -> Tuple[str, List[str]]:
#     """
#     Search the healthcare PDF leaflets knowledge base and return only the most relevant chunks.
#     """
#     global last_retrieved_context
#     scored_docs = vector_store.similarity_search_with_score(query, k=TOP_K)

#     chunks: List[str] = []
#     if scored_docs:
#         top_doc, top_score = scored_docs[0]
#         chunks.append(top_doc.page_content)

#         for doc, score in scored_docs[1:]:
#             if score >= MIN_SECOND_SCORE and (top_score - score) <= MAX_SCORE_GAP:
#                 chunks.append(doc.page_content)

#     last_retrieved_context = chunks
#     return "\n\n".join(chunks), chunks
