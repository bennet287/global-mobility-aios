"""
LangGraph skeleton for lead intake.

Install optional dependencies with:
    pip install -r requirements-ai.txt

This workflow is intentionally separated from the API routes so production execution can be versioned and tested.
"""
from typing import TypedDict, Optional


class IntakeState(TypedDict, total=False):
    raw_input: dict
    intent: str
    profile_status: str
    truth_status: str
    human_review_required: bool
    next_action: str


def classify_intent(state: IntakeState) -> IntakeState:
    raw = state.get("raw_input", {})
    text = " ".join(str(v).lower() for v in raw.values())
    if "visa" in text:
        intent = "visa"
    elif "job" in text or "work" in text:
        intent = "overseas_job"
    elif "study" in text or "university" in text:
        intent = "study_abroad"
    else:
        intent = "unknown"
    return {**state, "intent": intent}


def decide_review(state: IntakeState) -> IntakeState:
    intent = state.get("intent", "unknown")
    needs_review = intent in {"visa", "overseas_job"}
    return {
        **state,
        "truth_status": "required",
        "human_review_required": needs_review,
        "next_action": "truth_engine" if needs_review else "crm_followup",
    }


def build_graph():
    try:
        from langgraph.graph import StateGraph, END
    except ImportError as exc:
        raise RuntimeError("Install optional AI dependencies first: pip install -r requirements-ai.txt") from exc

    graph = StateGraph(IntakeState)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("decide_review", decide_review)
    graph.set_entry_point("classify_intent")
    graph.add_edge("classify_intent", "decide_review")
    graph.add_edge("decide_review", END)
    return graph.compile()
