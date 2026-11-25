import unittest

from app.services.ai_service import AIService


SAMPLE_INVOICE = """
FICTIONAL TEST DATA — NOT A REAL INVOICE
NORTHSTAR OFFICE SUPPLIES
TAX INVOICE
Invoice Number: INV-2026-1048
Invoice Date: 18 November 2026
Due Date: 18 December 2026
Purchase Order Number: PO-AT-2026-778
Vendor Name: Northstar Office Supplies
Vendor Address: 48 Meridian Business Park, Noida, Uttar Pradesh 201301, India
Vendor GSTIN: 09AABCN4821L1Z5
Customer Name: Asterion Technologies Private Limited
Customer Address: Sector 62, Noida, Uttar Pradesh 201309, India
Line items:
Business laptops, 14-inch, 16 GB RAM, 512 GB SSD
USB-C docking stations
Extended support and setup service
Subtotal
INR 465,000.00
CGST (9%)
INR 41,850.00
SGST (9%)
INR 41,850.00
GRAND TOTAL
INR 548,700.00
Payment terms: Net 30 days from invoice date.
Payment status: UNPAID
Currency: INR
"""


class InvoiceExtractionTests(unittest.TestCase):
    def setUp(self):
        self.service = AIService(provider="demo")

    def test_extracts_sample_invoice_fields(self):
        fields = self.service._extract_invoice_fields(SAMPLE_INVOICE)
        self.assertEqual(fields["Vendor"], "Northstar Office Supplies")
        self.assertEqual(fields["Invoice Number"], "INV-2026-1048")
        self.assertEqual(fields["Order Number"], "PO-AT-2026-778")
        self.assertEqual(fields["Invoice Date"], "18 November 2026")
        self.assertEqual(fields["Due Date"], "18 December 2026")
        self.assertEqual(fields["Subtotal"], "INR 465,000.00")
        self.assertEqual(fields["Tax"], "INR 83,700.00")
        self.assertEqual(fields["Total Amount"], "INR 548,700.00")
        self.assertEqual(fields["Customer"], "Asterion Technologies Private Limited")
        self.assertEqual(fields["Payment Terms"], "Net 30 days from invoice date.")
        self.assertEqual(fields["Payment Status"], "UNPAID")

    def test_unpaid_is_never_mistaken_for_paid(self):
        self.assertEqual(AIService._payment_status("Payment Status: UNPAID"), "UNPAID")
        self.assertEqual(AIService._payment_status("Invoice is unpaid."), "UNPAID")
        self.assertEqual(
            AIService._payment_status("Memo: the invoice will be paid next month."),
            "Not detected",
        )

    def test_explicit_paid_status_is_detected(self):
        self.assertEqual(AIService._payment_status("Payment Status: PAID"), "PAID")
        self.assertEqual(AIService._payment_status("PAID STAMP"), "PAID")

    def test_unpaid_invoice_routes_to_finance_approval(self):
        result = self.service._analyze_demo("sample_invoice.pdf", SAMPLE_INVOICE)
        self.assertEqual(result["extracted_fields"]["Payment Status"], "UNPAID")
        self.assertEqual(result["recommended_action"], "Finance Manager Approval")
        self.assertEqual(result["assigned_role"], "Finance Manager")

    def test_unknown_status_does_not_auto_archive(self):
        text = SAMPLE_INVOICE.replace("Payment status: UNPAID", "Payment status: NOT PROVIDED")
        result = self.service._analyze_demo("sample_invoice.pdf", text)
        self.assertEqual(result["extracted_fields"]["Payment Status"], "Not detected")
        self.assertEqual(result["recommended_action"], "MANUAL DOCUMENT VALIDATION")

    def test_demo_chat_answers_from_source_text(self):
        answer = self.service._chat_demo(SAMPLE_INVOICE, "What is the total amount?")
        self.assertIn("INR 548,700.00", answer)
        self.assertNotIn("93.50", answer)


if __name__ == "__main__":
    unittest.main()
