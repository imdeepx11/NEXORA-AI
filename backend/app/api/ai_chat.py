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

@router.post("/chat")
def chat_with_doc(req: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    doc = db.query(Document).filter(
        Document.id == req.document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    answer = AIService().chat_with_document(doc.extracted_text or "", req.question)

    return {
        "document_id": doc.id,
        "filename": doc.original_filename or doc.filename,
        "question": req.question,
        "answer": answer
    }

