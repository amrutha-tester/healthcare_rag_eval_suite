# Healthcare Chatbot — RAG & Promptfoo Evaluation

A Retrieval-Augmented Generation (RAG) healthcare assistant and automated evaluation suite built with **LangChain**, **PyMuPDF**, **Ollama / Google Gemini**, and **Promptfoo**.

The assistant answers patient questions strictly using a curated knowledge base of 10 verified healthcare and medication leaflets while enforcing clinical safety guardrails (emergency escalation, crisis support, no diagnosis/dosing fabrication, and strict grounding in retrieved context).

---

## Features

- **PDF Knowledge Base Ingestion**: Extracts and normalizes text blocks from 10 healthcare leaflet PDFs using `PyMuPDF` (`RAG1/file_reader.py`), tagging each chunk with its source leaflet identifier.
- **Dual-Provider Vector Indexing**: Supports local embeddings via **Ollama** (`nomic-embed-text`) for local development and **Google Gemini** (`models/gemini-embedding-001`) for CI/cloud environments (`RAG1/indexing.py`).
- **Safety-First Healthcare RAG**: Designed to handle medication guidance, pregnancy warnings, pediatric dosing rules, red-flag symptoms, and mental health crisis routing without hallucinating unsupported medical advice.
- **Automated Evaluation with Promptfoo**: Tests RAG faithfulness, context relevance, clinical safety, out-of-scope refusal (e.g., medications absent from the knowledge base), and formatting constraints.

---

## Knowledge Base (`data/leaflets/`)

The repository includes 10 patient information leaflets (reproducible via `scripts/generate_leaflets.py`):

| File | Topic |
| :--- | :--- |
| `01_medicine_and_pregnancy.pdf` | Medication safety during pregnancy (Paracetamol vs. NSAIDs/Ibuprofen) |
| `02_ibuprofen_leaflet.pdf` | Ibuprofen (Advil/Nurofen) uses, pregnancy warnings, weight-based pediatric dosing |
| `03_paracetamol_leaflet.pdf` | Paracetamol dosing, 4g daily maximum, liver toxicity warnings |
| `04_amoxicillin_antibiotics_leaflet.pdf` | Amoxicillin usage, bacterial vs. viral infections, completing the course |
| `05_vicks_vaporub_leaflet.pdf` | Vicks VapoRub external topical use only, age & application precautions |
| `06_aspirin_leaflet.pdf` | Aspirin uses, Reye's syndrome warning, GI bleeding & alcohol interaction |
| `07_first_aid_bleeding_anaphylaxis_stroke.pdf` | Emergency first aid (112, FAST stroke signs, EpiPen anaphylaxis, severe bleeding) |
| `08_symptom_red_flags_guide.pdf` | Clinical red flags (abdominal pain, eye emergencies, melanoma ABCDE, anaemia) |
| `09_mental_health_crisis_support.pdf` | European crisis hotlines (112, 3114, 1813) and immediate mental health support |
| `10_healthy_lifestyle_general_wellness.pdf` | Sleep, hydration, nutrition, physical activity, and preventive wellness |

---

## Project Structure

```text
RAG_evaluation/
├── data/
│   └── leaflets/                  # 10 verified healthcare patient leaflet PDFs
├── RAG1/
│   ├── file_reader.py             # PDF paragraph extraction and chunk tagging
│   └── indexing.py                # In-memory vector store setup (Ollama / Gemini)
├── scripts/
│   └── generate_leaflets.py       # Script to regenerate the 10 healthcare PDFs
├── src/
│   └── rag_evaluation/            # Package entry point
├── pyproject.toml                 # Python dependencies and uv build configuration
└── README.md
```

---

## Prerequisites

- **Python**: `>= 3.13`
- **[uv](https://docs.astral.sh/uv/)**: Fast Python package and environment manager
- **Embedding / LLM Provider** (choose one):
  - **Local (Default)**: [Ollama](https://ollama.com/) with `nomic-embed-text` pulled (`ollama pull nomic-embed-text`)
  - **Cloud / CI**: Google Gemini API key (`GEMINI_API_KEY` / `GOOGLE_API_KEY`)
- **[Node.js & Promptfoo](https://www.promptfoo.dev/)**: For running automated RAG and safety evaluations (`npx promptfoo@latest`)

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd RAG_evaluation
   ```

2. **Install Python dependencies with `uv`**:
   ```bash
   uv sync
   ```

3. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```env
   # Set to "ollama" (default) or "gemini"
   LLM_PROVIDER=ollama

   # Required if LLM_PROVIDER=gemini
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

4. **(Optional) Pull local Ollama models**:
   ```bash
   ollama pull nomic-embed-text
   ```

---

## Usage

### 1. Test PDF Paragraph Extraction
Verify that all 10 PDF leaflets are parsed and chunked properly:
```bash
uv run python RAG1/file_reader.py
```

### 2. Build and Verify the Vector Index
Embed the extracted paragraphs into the `InMemoryVectorStore`:
```bash
uv run python RAG1/indexing.py
```

### 3. Regenerate the Healthcare Leaflets (Optional)
If you need to rebuild the PDF dataset in `data/leaflets/`:
```bash
uv run python scripts/generate_leaflets.py
```

---

## Evaluation with Promptfoo

Promptfoo is used to evaluate the RAG pipeline across both **RAG quality metrics** and **healthcare safety guardrails**:

- **Knowledge Base Grounding**: Refuses to answer questions about medications not present in the leaflets (e.g., *zolpidem*) without guessing.
- **Medication Safety**: Flags NSAID/Ibuprofen risks during pregnancy, enforces weight-based pediatric dosing checks, and warns against exceeding 4g/day of paracetamol or mixing aspirin with alcohol.
- **Emergency & Crisis Escalation**: Directs life-threatening symptoms (stroke FAST, anaphylaxis, severe bleeding) to emergency services (`112`) and mental health crises to official helplines (`3114`, `1813`, `112`).

To run the Promptfoo evaluation suite (once your `promptfooconfig.yaml` is configured):

```bash
npx promptfoo@latest eval
```

View the interactive evaluation matrix in your browser:

```bash
npx promptfoo@latest view
```
