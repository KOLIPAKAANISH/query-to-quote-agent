import json
import os
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from agent.schemas import TripIntent, AgentState
from agent.prompts import (
    EXTRACT_SYSTEM, EXTRACT_HUMAN,
    CLASSIFY_SYSTEM, CLASSIFY_HUMAN,
    DRAFT_SYSTEM, DRAFT_HUMAN,
)
from data.seed_rates import search_rates

# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

def _get_llm(temperature: float = 0.1) -> ChatGroq:
    return ChatGroq(
        model="openai/gpt-oss-20b",
        groq_api_key=os.environ["GROQ_API_KEY"],
        temperature=temperature,
    )


# ---------------------------------------------------------------------------
# Node: Extract
# ---------------------------------------------------------------------------

def extract_node(state: AgentState) -> dict[str, Any]:
    """Extract structured TripIntent from the raw inquiry."""
    llm = _get_llm(temperature=0.0)

    messages = [
        SystemMessage(content=EXTRACT_SYSTEM),
        HumanMessage(content=EXTRACT_HUMAN.format(inquiry=state["raw_inquiry"])),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    try:
        data = json.loads(raw)
        intent = TripIntent(**data)
    except Exception:
        # Fallback: ask LLM to just give JSON
        intent = TripIntent(raw_notes=raw)

    return {"intent": intent}


# ---------------------------------------------------------------------------
# Node: Classify
# ---------------------------------------------------------------------------

def classify_node(state: AgentState) -> dict[str, Any]:
    """Classify lead quality based on extracted intent."""
    intent = state.get("intent")
    if intent is None:
        return {"lead_quality": "vague", "quality_reason": "Extraction failed"}

    # Rule-based pre-check
    fields = {
        "destination": intent.destination,
        "check_in": intent.check_in,
        "nights": intent.nights,
        "pax_count": intent.pax_count,
        "budget_inr": intent.budget_inr,
    }
    present = sum(1 for v in fields.values() if v is not None)
    has_dest = intent.destination is not None

    if has_dest and present >= 4:
        rule_quality = "hot"
    elif has_dest and present >= 2:
        rule_quality = "warm"
    else:
        rule_quality = "vague"

    # Use LLM to generate the reasoning
    llm = _get_llm(temperature=0.0)
    messages = [
        SystemMessage(content=CLASSIFY_SYSTEM),
        HumanMessage(content=CLASSIFY_HUMAN.format(
            destination=intent.destination,
            check_in=intent.check_in,
            nights=intent.nights,
            pax_count=intent.pax_count,
            budget_inr=intent.budget_inr,
            needs=intent.needs,
        )),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    try:
        data = json.loads(raw)
        quality = data.get("quality", rule_quality)
        reason = data.get("reason", "LLM classification")
    except Exception:
        quality = rule_quality
        reason = f"Rule-based classification: {present} fields present"

    return {"lead_quality": quality, "quality_reason": reason}


# ---------------------------------------------------------------------------
# Node: Retrieve (placeholder — will use ChromaDB in step 5)
# ---------------------------------------------------------------------------

def retrieve_node(state: AgentState) -> dict[str, Any]:
    """Retrieve relevant supplier rates from ChromaDB."""
    intent = state.get("intent")
    if intent is None:
        return {"retrieved_rates": []}

    # Build query from destination + needs
    parts = []
    if intent.destination:
        parts.append(intent.destination)
    if intent.needs:
        parts.extend(intent.needs)
    query = " ".join(parts) if parts else state["raw_inquiry"]

    rates = search_rates(query, n_results=3)
    return {"retrieved_rates": rates}


# ---------------------------------------------------------------------------
# Node: Draft
# ---------------------------------------------------------------------------

def draft_node(state: AgentState) -> dict[str, Any]:
    """Generate supplier request and client acknowledgment."""
    intent = state.get("intent")
    if intent is None:
        return {
            "supplier_request": "(Intent extraction failed — cannot draft)",
            "client_ack": "(Intent extraction failed — cannot draft)",
        }

    rates = state.get("retrieved_rates", [])
    rates_text = "\n".join(f"- {r}" for r in rates) if rates else "No rates retrieved."

    llm = _get_llm(temperature=0.4)
    messages = [
        SystemMessage(content=DRAFT_SYSTEM),
        HumanMessage(content=DRAFT_HUMAN.format(
            destination=intent.destination,
            check_in=intent.check_in,
            nights=intent.nights,
            pax_count=intent.pax_count,
            budget_inr=intent.budget_inr,
            needs=", ".join(intent.needs) if intent.needs else "Not specified",
            lead_quality=state.get("lead_quality", "unknown"),
            rates=rates_text,
        )),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    try:
        data = json.loads(raw)
        supplier_request = data.get("supplier_request", "")
        client_ack = data.get("client_ack", "")
    except Exception:
        supplier_request = raw
        client_ack = "(Failed to parse draft response)"

    return {
        "supplier_request": supplier_request,
        "client_ack": client_ack,
    }


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("extract", extract_node)
    graph.add_node("classify", classify_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("draft", draft_node)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "draft")
    graph.add_edge("draft", END)

    return graph.compile()
