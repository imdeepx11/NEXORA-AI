import unittest

from app.api.ai_chat import ChatRequest


class AIChatRequestSchemaTests(unittest.TestCase):
    def test_accepts_numeric_document_id_sent_by_frontend(self):
        request = ChatRequest.model_validate({
            "document_id": 123,
            "question": "What is the total amount?",
        })
        self.assertEqual(request.document_id, 123)
        self.assertEqual(request.question, "What is the total amount?")

    def test_accepts_string_document_id_for_compatibility(self):
        request = ChatRequest.model_validate({
            "document_id": "123",
            "question": "What is the payment status?",
        })
        self.assertEqual(request.document_id, 123)


if __name__ == "__main__":
    unittest.main()
