# Query-to-Quote Agent

A mini version of Flyo.ai's Query & Quotation Agent. Takes a raw travel inquiry, extracts structured intent, classifies lead quality, retrieves supplier rates via RAG, and drafts both a supplier-facing quote request and a client-facing acknowledgment.

## Tech Stack

- **Python 3.11+**
- **LangGraph** — multi-step agent flow orchestration
- **LangChain** — LLM wrapper, prompt templates
- **Groq** — fast inference (openai/gpt-oss-20b)
- **ChromaDB** — vector store for supplier rate RAG
- **Flask** — single-page UI + REST endpoint
- **Pydantic** — structured output schemas

## Setup

```bash
# 1. Clone and install dependencies
cd query-to-quote-agent
pip install -r requirements.txt

# 2. Set your Groq API key (free at console.groq.com)
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 3. Run the app
python app.py
```

Open http://localhost:5000 in your browser.

## Agent Flow

```
[Raw Inquiry] → Extract → Classify → Retrieve (RAG) → Draft
                    ↓          ↓            ↓              ↓
               TripIntent   Lead       Supplier        Two drafted
               (Pydantic)   Quality     Rates         messages
```

## API

- `GET /` — UI form
- `POST /process` — Run the agent pipeline (JSON body: `{"inquiry": "..."}`)
