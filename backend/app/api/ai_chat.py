from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Document, User
from app.services.ai_service import AIService

from app.api.auth import require_auth

router = APIRouter(prefix="/api/ai", tags=["ai"], dependencies=[Depends(require_auth)])

class ChatRequest(BaseModel):
    # The frontend sends the database document ID as a JSON number.
    # Keep this typed as int so Pydantic v2 does not reject the request with 422.
    document_id: int
    question: str


def _answer_from_analysis_context(question: str, analysis) -> str | None:
    """Answer risk and approval questions from this document's saved NEXORA analysis."""
    if analysis is None:
        return None

    q = (question or "").casefold()
    get_value = (
        analysis.get
        if isinstance(analysis, dict)
        else lambda key, default=None: getattr(analysis, key, default)
    )

    risk_terms = ("risk", "flagged signal", "risk score", "risk level")
    approval_terms = (
        "who approves", "who is the approver", "approver", "approval",
        "assigned role", "who handles", "who reviews",
    )
    priority_terms = ("routing priority", "priority", "how urgent")

    if any(term in q for term in risk_terms):
        score = get_value("risk_score")
        level = get_value("risk_level")
        signals = get_value("risks") or []
        priority = get_value("priority")

        score_text = f"{score}/100" if score is not None else "not recorded"
        level_text = str(level).title() if level else "not recorded"
        if isinstance(signals, list):
            descriptions = [
                str(item.get("text", "")).strip()
                for item in signals
                if isinstance(item, dict) and item.get("text")
            ]
        else:
            descriptions = []

        if descriptions:
            signal_text = " ".join(
                f"{index}. {description}"
                for index, description in enumerate(descriptions, start=1)
            )
        else:
            signal_text = "No explicit flagged signals are recorded."

        priority_text = f" Routing priority: {priority}." if priority else ""
        return (
            f"NEXORA AI assessed this document as {level_text} risk "
            f"({score_text}). Flagged signals: {signal_text}{priority_text}"
        )

    if any(term in q for term in approval_terms):
        role = get_value("assigned_role")
        action = get_value("recommended_action")
        sla = get_value("sla_hours")
        reason = get_value("priority_reason")

        parts = []
        if action:
            parts.append(f"Recommended action: {action}.")
        if role:
            parts.append(f"Assigned approver/role: {role}.")
        if sla is not None:
            parts.append(f"Target SLA: {sla} hours.")
        if reason:
            parts.append(f"Reason: {reason}")
        return " ".join(parts) if parts else "No approval assignment is recorded for this document."

    if any(term in q for term in priority_terms):
        priority = get_value("priority")
        reason = get_value("priority_reason")
        if priority or reason:
            parts = []
            if priority:
                parts.append(f"Routing priority: {priority}.")
            if reason:
                parts.append(f"Reason: {reason}")
            return " ".join(parts)

    return None

@router.post("/chat")
def chat_with_doc(req: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    doc = db.query(Document).filter(
        Document.id == req.document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Use the saved NEXORA analysis for calculated risk and routing questions.
    # All other questions remain grounded in the original extracted document text.
    answer = _answer_from_analysis_context(req.question, doc.analysis)
    if answer is None:
        answer = AIService().chat_with_document(doc.extracted_text or "", req.question)

    return {
        "document_id": doc.id,
        "filename": doc.original_filename or doc.filename,
        "question": req.question,
        "answer": answer
    }

