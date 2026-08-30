from typing import TypedDict, Optional, Literal
from pydantic import BaseModel


class TripIntent(BaseModel):
    destination: Optional[str] = None
    check_in: Optional[str] = None       # ISO date or None if unclear
    nights: Optional[int] = None
    pax_count: Optional[int] = None
    budget_inr: Optional[int] = None
    needs: list[str] = []                # e.g. ["flights", "resort", "activities"]
    raw_notes: Optional[str] = None      # anything extracted but not fitting above


class AgentState(TypedDict):
    raw_inquiry: str
    intent: Optional[TripIntent]
    lead_quality: Optional[Literal["hot", "warm", "vague"]]
    quality_reason: Optional[str]
    retrieved_rates: Optional[list[str]]
    supplier_request: Optional[str]
    client_ack: Optional[str]
