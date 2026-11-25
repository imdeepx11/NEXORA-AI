import unittest
from types import SimpleNamespace

from app.api.ai_chat import _answer_from_analysis_context


ANALYSIS = SimpleNamespace(
    risk_score=45,
    risk_level="MEDIUM",
    risks=[
        {
            "type": "WARNING",
            "text": "Invoice is explicitly marked UNPAID and requires finance approval.",
        }
    ],
    priority="HIGH",
    assigned_role="Finance Manager",
    recommended_action="Finance Manager Approval",
    sla_hours=24,
    priority_reason=(
        "The source explicitly marks this invoice as UNPAID; "
        "finance approval is required before payment."
    ),
)


class AnalysisContextChatTests(unittest.TestCase):
    def test_risk_question_uses_saved_risk_assessment(self):
        answer = _answer_from_analysis_context("What are the risks?", ANALYSIS)
        self.assertIn("Medium risk", answer)
        self.assertIn("45/100", answer)
        self.assertIn("UNPAID", answer)
        self.assertIn("HIGH", answer)

    def test_approval_question_returns_assigned_approver_and_sla(self):
        answer = _answer_from_analysis_context(
            "Who approves this invoice?", ANALYSIS
        )
        self.assertIn("Finance Manager Approval", answer)
        self.assertIn("Finance Manager", answer)
        self.assertIn("24 hours", answer)

    def test_priority_question_returns_saved_routing_priority(self):
        answer = _answer_from_analysis_context(
            "What is the routing priority?", ANALYSIS
        )
        self.assertIn("HIGH", answer)
        self.assertIn("UNPAID", answer)

    def test_document_fact_questions_fall_through_to_document_chat(self):
        answer = _answer_from_analysis_context(
            "What is the total amount?", ANALYSIS
        )
        self.assertIsNone(answer)

    def test_missing_analysis_falls_through_safely(self):
        answer = _answer_from_analysis_context("What are the risks?", None)
        self.assertIsNone(answer)


if __name__ == "__main__":
    unittest.main()
