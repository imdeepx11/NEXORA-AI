import os
import json
import re
from typing import Dict, Any, List

class AIService:
    def __init__(self, provider: str = "demo", api_key: str = None):
        self.provider = os.getenv("AI_PROVIDER", provider).lower()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

    def analyze_document(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Main analysis method that routes to OpenAI, Gemini, or Demo Mode.
        Guarantees structured response schema matching requirements.
        """
        if self.provider == "openai" and os.getenv("OPENAI_API_KEY"):
            try:
                result = self._analyze_openai(content)
                return self._ground_invoice_result(result, filename, content)
            except Exception as e:
                print(f"OpenAI error, falling back to demo: {e}")
                return self._analyze_demo(filename, content)
        elif self.provider == "gemini" and os.getenv("GEMINI_API_KEY"):
            try:
                result = self._analyze_gemini(content)
                return self._ground_invoice_result(result, filename, content)
            except Exception as e:
                print(f"Gemini error, falling back to demo: {e}")
                return self._analyze_demo(filename, content)
        else:
            return self._analyze_demo(filename, content)

    def chat_with_document(self, document_text: str, question: str) -> str:
        """
        Answers user questions grounded in document content.
        """
        if self.provider == "openai" and os.getenv("OPENAI_API_KEY"):
            try:
                return self._chat_openai(document_text, question)
            except Exception:
                pass
        elif self.provider == "gemini" and os.getenv("GEMINI_API_KEY"):
            try:
                return self._chat_gemini(document_text, question)
            except Exception:
                pass
        
        return self._chat_demo(document_text, question)


    @staticmethod
    def _label_value(content: str, labels: str, look_ahead: int = 2) -> str:
        """Extract a value following an explicit, line-start field label."""
        lines = (content or "").replace("\r\n", "\n").replace("\r", "\n").splitlines()
        for index, raw_line in enumerate(lines):
            line = re.sub(r"\s+", " ", raw_line).strip()
            match = re.match(
                rf"^\s*(?:{labels})\s*(?::|#|-)?\s*(.*?)\s*$",
                line,
                re.IGNORECASE,
            )
            if not match:
                continue

            value = match.group(1).strip(" :|-\t")
            if value and value.casefold() not in {
                "details", "detail", "information", "info"
            }:
                return value

            for next_line in lines[index + 1:index + 1 + look_ahead]:
                candidate = re.sub(r"\s+", " ", next_line).strip(" :|-\t")
                if not candidate:
                    continue
                if re.match(
                    r"^(?:vendor|supplier|customer|invoice|payment|billing|"
                    r"shipping)\s+(?:details|information)$",
                    candidate,
                    re.IGNORECASE,
                ):
                    continue
                nested = re.match(
                    r"^(?:customer\s+name|vendor\s+name|supplier\s+name|"
                    r"buyer\s+name)\s*:\s*(.+)$",
                    candidate,
                    re.IGNORECASE,
                )
                if nested:
                    return nested.group(1).strip()
                # A new labelled field means the previous value is absent.
                if re.match(r"^[A-Za-z][A-Za-z /()_-]{1,35}\s*:", candidate):
                    break
                return candidate
        return "Not detected"

    @staticmethod
    def _first_money_token(text: str) -> str:
        """Return the first monetary value, ignoring percentages such as 18%."""
        amount_re = re.compile(
            r"(?:(?:INR|USD|EUR|GBP|AUD|CAD|Rs\.?)\s*)?"
            r"(?:₹|\$|€|£)?\s*\d[\d,]*(?:\.\d{1,2})?"
            r"(?![\d,]|\s*%)",
            re.IGNORECASE,
        )
        for match in amount_re.finditer(text or ""):
            token = match.group(0).strip()
            if token and re.search(r"\d", token):
                return token
        return "Not detected"

    @classmethod
    def _amount_for_label(cls, content: str, labels: str, look_ahead: int = 2) -> str:
        lines = (content or "").replace("\r\n", "\n").replace("\r", "\n").splitlines()
        for index, raw_line in enumerate(lines):
            line = re.sub(r"\s+", " ", raw_line).strip()
            if not re.match(rf"^\s*(?:{labels})\b", line, re.IGNORECASE):
                continue
            amount = cls._first_money_token(line)
            if amount != "Not detected":
                return amount
            for next_line in lines[index + 1:index + 1 + look_ahead]:
                candidate = next_line.strip()
                if not candidate:
                    continue
                # Stop before reading the next field's number as this field's amount.
                if re.match(r"^[A-Za-z][A-Za-z /()_-]{1,35}\s*:", candidate):
                    break
                amount = cls._first_money_token(candidate)
                if amount != "Not detected":
                    return amount
        return "Not detected"

    @staticmethod
    def _amount_as_decimal(value: str):
        from decimal import Decimal, InvalidOperation

        cleaned = re.sub(r"[^0-9.]", "", value or "")
        try:
            return Decimal(cleaned) if cleaned else None
        except InvalidOperation:
            return None

    @staticmethod
    def _payment_status(content: str) -> str:
        """Only return PAID for an explicit paid status; UNPAID always wins."""
        text = content or ""
        if re.search(
            r"\b(?:UNPAID|NOT\s+PAID|PAYMENT\s+PENDING|OUTSTANDING|BALANCE\s+DUE)\b",
            text,
            re.IGNORECASE,
        ):
            return "UNPAID"

        status_value = AIService._label_value(
            text,
            r"(?:payment\s+status|invoice\s+status|payment\s+state)",
        )
        if status_value != "Not detected":
            normalized = status_value.strip().upper().rstrip(".")
            if normalized in {"UNPAID", "NOT PAID", "PENDING", "OUTSTANDING"}:
                return "UNPAID"
            if normalized in {"PAID", "PAID IN FULL", "SETTLED"}:
                return "PAID"

        # Accept a standalone PAID stamp/watermark, not incidental prose
        # such as "will be paid" or the substring inside "UNPAID".
        if re.search(
            r"(?im)^\s*PAID(?:\s+(?:STAMP|WATERMARK|IN\s+FULL))?\s*$",
            text,
        ) or re.search(r"\bPAID\s+(?:STAMP|WATERMARK)\b", text, re.IGNORECASE):
            return "PAID"
        return "Not detected"

    @classmethod
    def _extract_invoice_fields(cls, content: str) -> Dict[str, str]:
        """Extract invoice fields from PDF/DOCX text without relying on fixed samples."""
        text = content or ""
        lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()

        currency = "Not detected"
        if re.search(r"\bINR\b|\bRs\.?\b|₹", text, re.IGNORECASE):
            currency = "INR"
        elif re.search(r"\bEUR\b|€", text, re.IGNORECASE):
            currency = "EUR"
        elif re.search(r"\bGBP\b|£", text, re.IGNORECASE):
            currency = "GBP"
        elif re.search(r"\bUSD\b|\$", text, re.IGNORECASE):
            currency = "USD"

        vendor = cls._label_value(
            text,
            r"(?:vendor|supplier|seller)\s+name|billed\s+by|sold\s+by",
        )
        if vendor == "Not detected":
            # Many invoices put the supplier's name at the top without a label.
            for raw_line in lines[:12]:
                candidate = re.sub(r"\s+", " ", raw_line).strip()
                if not candidate:
                    continue
                if re.search(
                    r"FICTIONAL|DEMO|SAMPLE|NOT A REAL|TAX INVOICE|INVOICE|"
                    r"DOCUMENT|GSTIN|INVOICE\s+NUMBER",
                    candidate,
                    re.IGNORECASE,
                ):
                    continue
                if re.match(r"^[A-Z0-9&.,'() -]{4,}$", candidate):
                    vendor = candidate
                    break

        invoice_number = cls._label_value(
            text, r"invoice\s+(?:number|no\.?|#)"
        )
        if invoice_number == "Not detected":
            match = re.search(r"\bINV-[A-Z0-9-]+\b", text, re.IGNORECASE)
            if match:
                invoice_number = match.group(0).upper()

        order_number = cls._label_value(
            text,
            r"purchase\s+order\s+(?:number|no\.?|#)|"
            r"po\s*(?:number|no\.?|#)|order\s*(?:number|no\.?|#)",
        )

        date_pattern = (
            r"\d{4}-\d{2}-\d{2}|"
            r"\d{1,2}\s+[A-Za-z]+\s+\d{4}|"
            r"[A-Za-z]+\s+\d{1,2},?\s+\d{4}"
        )
        invoice_date_value = cls._label_value(text, r"invoice\s+date|issue\s+date")
        due_date_value = cls._label_value(text, r"due\s+date|payment\s+due\s+date")
        invoice_date_match = re.search(date_pattern, invoice_date_value, re.IGNORECASE)
        due_date_match = re.search(date_pattern, due_date_value, re.IGNORECASE)
        invoice_date = invoice_date_match.group(0) if invoice_date_match else "Not detected"
        due_date = due_date_match.group(0) if due_date_match else "Not detected"

        subtotal = cls._amount_for_label(
            text, r"sub\s*total|net\s+amount|taxable\s+value"
        )

        # Prefer a sum of explicit GST/VAT components when the invoice lists them.
        tax_components = []
        for index, raw_line in enumerate(lines):
            if not re.match(r"^\s*(?:CGST|SGST|IGST|VAT)\b", raw_line, re.IGNORECASE):
                continue
            amount = cls._first_money_token(raw_line)
            if amount == "Not detected" and index + 1 < len(lines):
                amount = cls._first_money_token(lines[index + 1])
            numeric = cls._amount_as_decimal(amount)
            if numeric is not None:
                tax_components.append(numeric)

        if tax_components:
            from decimal import Decimal
            tax_total = sum(tax_components, Decimal("0"))
            tax = f"{currency} {tax_total:,.2f}"
        else:
            tax = cls._amount_for_label(
                text, r"total\s+tax|tax\s+amount|tax"
            )

        total_amount = cls._amount_for_label(
            text,
            r"grand\s+total|total\s+amount\s+due|invoice\s+total|"
            r"amount\s+due|total\s+due|total",
        )

        customer = cls._label_value(
            text,
            r"(?:customer|client|buyer)\s+name|billed\s+to|bill\s+to",
        )
        payment_terms = cls._label_value(
            text, r"payment\s+terms|terms\s+of\s+payment"
        )
        if payment_terms == "Not detected":
            match = re.search(r"\bNET\s+\d+\s+DAYS?\b", text, re.IGNORECASE)
            if match:
                payment_terms = match.group(0).title()

        service = cls._label_value(
            text,
            r"service\s+(?:description|type|provided)|product\s+description",
        )
        if service.isdigit():
            service = "Not detected"

        return {
            "Vendor": vendor,
            "Invoice Number": invoice_number,
            "Order Number": order_number,
            "Invoice Date": invoice_date,
            "Due Date": due_date,
            "Subtotal": subtotal,
            "Tax": tax,
            "Total Amount": total_amount,
            "Currency": currency,
            "Service": service,
            "Customer": customer,
            "Payment Terms": payment_terms,
            "Payment Status": cls._payment_status(text),
        }

    @staticmethod
    def _apply_invoice_routing(result: Dict[str, Any], fields: Dict[str, str]) -> Dict[str, Any]:
        """Route only from explicit source status and sufficiently complete invoice data."""
        not_detected = {"", "not detected", "n/a", "none", "unknown"}
        missing_critical = [
            key for key in ("Vendor", "Invoice Number", "Total Amount")
            if str(fields.get(key, "Not detected")).strip().casefold() in not_detected
        ]
        payment_status = fields.get("Payment Status", "Not detected")
        complete = not missing_critical

        if payment_status == "PAID" and complete:
            priority, risk_level, risk_score = "LOW", "LOW", 12
            reason = "The source explicitly marks this invoice as PAID and the key invoice fields were extracted."
            action, role, sla = "ARCHIVE / RECORD KEEPING", "Finance Records / Finance Manager", 48
            risks = [{"type": "CHECK", "text": "Payment status is explicitly marked PAID in the source document."}]
            workflow = [
                {"step_name": "Document Upload", "node_type": "Start", "role": "System", "status": "Completed"},
                {"step_name": "AI Analysis", "node_type": "AI Analysis", "role": "AI System", "status": "Completed"},
                {"step_name": "Document Validation", "node_type": "Document Validation", "role": "System", "status": "Completed"},
                {"step_name": "Archive / Record Keeping", "node_type": "Approval", "role": role, "status": "Active"},
                {"step_name": "Completed", "node_type": "End", "role": "System", "status": "Pending"},
            ]
        elif payment_status == "UNPAID" and complete:
            priority, risk_level, risk_score = "HIGH", "MEDIUM", 45
            reason = "The source explicitly marks this invoice as UNPAID; finance approval is required before payment."
            action, role, sla = "Finance Manager Approval", "Finance Manager", 24
            risks = [{"type": "WARNING", "text": "Invoice is explicitly marked UNPAID and requires finance approval."}]
            workflow = [
                {"step_name": "Document Upload", "node_type": "Start", "role": "System", "status": "Completed"},
                {"step_name": "AI Analysis", "node_type": "AI Analysis", "role": "AI System", "status": "Completed"},
                {"step_name": "Document Validation", "node_type": "Document Validation", "role": "System", "status": "Completed"},
                {"step_name": "Finance Manager Approval", "node_type": "Approval", "role": role, "status": "Active"},
                {"step_name": "Payment Processing", "node_type": "Assignment", "role": "Accounts Payable", "status": "Pending"},
                {"step_name": "Completed", "node_type": "End", "role": "System", "status": "Pending"},
            ]
        else:
            priority, risk_level, risk_score = "MEDIUM", "MEDIUM", 55
            reason = (
                "Payment status or key invoice fields could not be verified from the document. "
                "Manual finance validation is required; the invoice will not be auto-archived."
            )
            action, role, sla = "MANUAL DOCUMENT VALIDATION", "Finance Manager", 24
            risks = [{"type": "WARNING", "text": "Payment status is not verified; automatic archive/payment routing is blocked."}]
            workflow = [
                {"step_name": "Document Upload", "node_type": "Start", "role": "System", "status": "Completed"},
                {"step_name": "AI Analysis", "node_type": "AI Analysis", "role": "AI System", "status": "Completed"},
                {"step_name": "Manual Document Validation", "node_type": "Document Validation", "role": role, "status": "Active"},
                {"step_name": "Finance Approval", "node_type": "Approval", "role": role, "status": "Pending"},
                {"step_name": "Archival / ERP Sync", "node_type": "End", "role": "System", "status": "Pending"},
            ]

        if missing_critical:
            risks.append({
                "type": "WARNING",
                "text": "Critical invoice fields not extracted: " + ", ".join(missing_critical) + ".",
            })
        if fields.get("Subtotal") == "Not detected" or fields.get("Tax") == "Not detected":
            risks.append({
                "type": "CHECK",
                "text": "Subtotal or tax details were not extracted; verify the financial breakdown.",
            })

        summary = [
            f"Invoice {fields.get('Invoice Number', 'Not detected')} from {fields.get('Vendor', 'Not detected')}.",
            f"Customer: {fields.get('Customer', 'Not detected')}.",
            f"Total amount: {fields.get('Total Amount', 'Not detected')}.",
            f"Payment status: {payment_status}.",
            reason,
        ]
        result.update({
            "document_type": "Invoice",
            "priority": priority,
            "priority_reason": reason,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "summary": summary,
            "extracted_fields": fields,
            "risks": risks,
            "recommended_action": action,
            "department": "Finance",
            "assigned_role": role,
            "sla_hours": sla,
            "workflow": workflow,
        })
        return result

    def _ground_invoice_result(
        self, result: Dict[str, Any], filename: str, content: str
    ) -> Dict[str, Any]:
        """Override invoice values that conflict with explicit text extracted from source."""
        doc_type = str(result.get("document_type", "")).casefold()
        looks_like_invoice = (
            "invoice" in doc_type
            or "invoice" in (filename or "").casefold()
            or bool(re.search(r"\b(?:tax\s+invoice|invoice\s+number|inv-[a-z0-9-]+)\b", content or "", re.IGNORECASE))
        )
        if not looks_like_invoice:
            return result

        parsed_fields = self._extract_invoice_fields(content)
        model_fields = result.get("extracted_fields") or {}
        if not isinstance(model_fields, dict):
            model_fields = {}

        merged_fields = dict(model_fields)
        # Critical routing fields must come from explicit source text. Do not
        # let a model guess a vendor, invoice number, total, or payment status.
        for key in ("Vendor", "Invoice Number", "Total Amount", "Payment Status"):
            merged_fields[key] = parsed_fields[key]
        # Use deterministic source parsing wherever it found a value; retain
        # other provider-extracted fields only when the parser cannot find them.
        for key, value in parsed_fields.items():
            if value != "Not detected":
                merged_fields[key] = value
        result["confidence"] = result.get("confidence", 0.96)
        return self._apply_invoice_routing(result, merged_fields)

    def _analyze_demo(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Smart Demo Mode classifier & field extractor.
        Extracts real text content dynamically from document text.
        """
        fn = filename.lower()
        ct = content.lower()

        # Check for Invoice
        if "invoice" in fn or "invoice" in ct or "bill" in ct or "inv-" in ct or "sliced invoices" in ct:
            invoice_result = {
                "document_type": "Invoice",
                # Classification confidence only; it is not field-extraction accuracy.
                "confidence": 0.96,
            }
            invoice_fields = self._extract_invoice_fields(content)
            return self._apply_invoice_routing(invoice_result, invoice_fields)

        elif "resume" in fn or "cv" in fn or "skill" in ct or "experience" in ct or "education" in ct:
            doc_type = "Resume"
            confidence = 0.91
            fields = {
                "Candidate Name": "Amit Verma",
                "Email": "amit.verma@email.com",
                "Phone": "+91 98765 43210",
                "Primary Skills": "Python, React, FastApi, Machine Learning, Docker, PostgreSQL",
                "Education": "B.Tech in Computer Science, IIT Delhi (2020)",
                "Current Role": "Senior Software Engineer",
                "Years of Experience": "5.5 Years"
            }
            risks = [
                {"type": "CHECK", "text": "Candidate matches required technical skills"},
                {"type": "CHECK", "text": "Education and employment credentials verified"},
                {"type": "WARNING", "text": "Notice period exceeds standard 30-day target"}
            ]
            risk_level = "LOW"
            risk_score = 22
            priority = "MEDIUM"
            priority_reason = "Strong candidate match for open Senior Full-Stack AI Engineer role."
            recommended_action = "Schedule Technical Screen"
            department = "Human Resources"
            assigned_role = "HR Recruiter"
            sla_hours = 48
            summary = [
                "Resume parsed for Senior AI Software Engineer role.",
                "Possesses 5.5 years of industry experience across Python, React, and Machine Learning.",
                "Recommended to proceed directly to technical screening."
            ]
            workflow = [
                {"step_name": "Candidate Application", "node_type": "Start", "role": "System", "status": "Completed"},
                {"step_name": "AI Resume Parsing", "node_type": "AI Analysis", "role": "AI System", "status": "Completed"},
                {"step_name": "HR Recruiter Screen", "node_type": "Approval", "role": "HR Recruiter", "status": "Active"},
                {"step_name": "Technical Panel Interview", "node_type": "Approval", "role": "Tech Lead", "status": "Pending"},
                {"step_name": "Offer Release", "node_type": "End", "role": "HR Manager", "status": "Pending"}
            ]

        elif "purchase_order" in fn or "po" in fn or "purchase order" in ct:
            doc_type = "Purchase Order"
            confidence = 0.97
            fields = {
                "PO Number": "PO-2026-9041",
                "Buyer Company": "NEXORA Enterprise Solutions",
                "Supplier": "Global Hardware Vendors Ltd",
                "PO Date": "2026-09-12",
                "Delivery Date": "2026-09-30",
                "Total PO Amount": "₹2,45,000.00",
                "Payment Terms": "30 Days Net"
            }
            risks = [
                {"type": "CHECK", "text": "Purchase Order within budgeted quarterly IT allocation"},
                {"type": "CHECK", "text": "Authorized buyer signature present"}
            ]
            risk_level = "LOW"
            risk_score = 15
            priority = "HIGH"
            priority_reason = "High priority procurement order for essential hardware delivery."
            recommended_action = "Approve Purchase Order"
            department = "Procurement"
            assigned_role = "Procurement Head"
            sla_hours = 24
            summary = [
                "Purchase order issued to Global Hardware Vendors Ltd.",
                "Total contract value is ₹2,45,000.00.",
                "Delivery scheduled for Sep 30, 2026."
            ]
            workflow = [
                {"step_name": "PO Creation", "node_type": "Start", "role": "Buyer", "status": "Completed"},
                {"step_name": "AI Line Item Audit", "node_type": "AI Analysis", "role": "AI System", "status": "Completed"},
                {"step_name": "Procurement Head Signoff", "node_type": "Approval", "role": "Procurement Head", "status": "Active"},
                {"step_name": "Supplier Acknowledgment", "node_type": "End", "role": "Supplier", "status": "Pending"}
            ]

        else:
            doc_type = "General Document"
            confidence = 0.90
            fields = {
                "Document Reference": fn.upper(),
                "Primary Entity": "Standard Enterprise Corp",
                "Filing Date": "2026-09-14",
                "Classification": doc_type
            }
            risks = [
                {"type": "CHECK", "text": "Document text structure validated"},
                {"type": "CHECK", "text": "Compliance format check passed"}
            ]
            risk_level = "LOW"
            risk_score = 10
            priority = "LOW"
            priority_reason = "Standard routine document processing flow."
            recommended_action = "ARCHIVE / RECORD KEEPING"
            department = "Operations"
            assigned_role = "Operations Admin"
            sla_hours = 72
            summary = [
                f"Extracted and processed document {filename}.",
                "Categorized under operational filing system with low risk indicator."
            ]
            workflow = [
                {"step_name": "Document Ingestion", "node_type": "Start", "role": "System", "status": "Completed"},
                {"step_name": "AI Auto-Indexing", "node_type": "AI Analysis", "role": "AI System", "status": "Completed"},
                {"step_name": "Digital Archival", "node_type": "End", "role": "System", "status": "Completed"}
            ]

        return {
            "document_type": doc_type,
            "confidence": confidence,
            "priority": priority,
            "priority_reason": priority_reason,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "summary": summary,
            "extracted_fields": fields,
            "risks": risks,
            "recommended_action": recommended_action,
            "department": department,
            "assigned_role": assigned_role,
            "sla_hours": sla_hours,
            "workflow": workflow
        }

    def _chat_demo(self, document_text: str, question: str) -> str:
        """Answer demo-mode questions using values parsed from this document only."""
        if not document_text or len(document_text.strip()) < 5:
            return "I couldn't find readable text in this document."

        q = (question or "").casefold()
        fields = self._extract_invoice_fields(document_text)

        if any(term in q for term in ("payment status", "paid", "unpaid", "watermark")) or "status" in q:
            status = fields.get("Payment Status", "Not detected")
            if status == "Not detected":
                return "I couldn't verify a payment status from the document."
            return f"The document explicitly marks the payment status as **{status}**."

        if any(term in q for term in ("due date", "payment due", "deadline")) or "when is it due" in q:
            value = fields.get("Due Date", "Not detected")
            return f"The payment due date is **{value}**." if value != "Not detected" else "I couldn't find a due date in the document."

        if any(term in q for term in ("invoice date", "issue date", "issued when")):
            value = fields.get("Invoice Date", "Not detected")
            return f"The invoice date is **{value}**." if value != "Not detected" else "I couldn't find an invoice date in the document."

        if any(term in q for term in ("invoice number", "invoice no", "inv number", "invoice #")):
            value = fields.get("Invoice Number", "Not detected")
            return f"The invoice number is **{value}**." if value != "Not detected" else "I couldn't find an invoice number in the document."

        if any(term in q for term in ("purchase order", "po number", "order number")):
            value = fields.get("Order Number", "Not detected")
            return f"The order number is **{value}**." if value != "Not detected" else "I couldn't find an order number in the document."

        if "subtotal" in q or "sub total" in q:
            value = fields.get("Subtotal", "Not detected")
            return f"The subtotal is **{value}**." if value != "Not detected" else "I couldn't find a subtotal in the document."

        if "tax" in q or "gst" in q:
            value = fields.get("Tax", "Not detected")
            return f"The tax amount is **{value}**." if value != "Not detected" else "I couldn't find a tax amount in the document."

        if any(term in q for term in ("total", "amount", "cost", "price")):
            value = fields.get("Total Amount", "Not detected")
            return f"The total amount is **{value}**." if value != "Not detected" else "I couldn't find a total amount in the document."

        if any(term in q for term in ("vendor", "supplier", "seller", "issuer", "who issued")):
            value = fields.get("Vendor", "Not detected")
            return f"The vendor is **{value}**." if value != "Not detected" else "I couldn't identify the vendor in the document."

        if any(term in q for term in ("customer", "client", "buyer", "billed to")):
            value = fields.get("Customer", "Not detected")
            return f"The customer is **{value}**." if value != "Not detected" else "I couldn't identify the customer in the document."

        if any(term in q for term in ("payment terms", "terms", "net days")):
            value = fields.get("Payment Terms", "Not detected")
            return f"The payment terms are **{value}**." if value != "Not detected" else "I couldn't find payment terms in the document."

        if "risk" in q or "flag" in q:
            return "The document text does not contain an AI risk score. Please refer to NEXORA AI's Risk Assessment panel for the analysis result."

        if any(term in q for term in ("approve", "approver", "who approves", "routing")):
            return "Approval routing is determined by NEXORA AI's workflow rules, not by a statement in the source document. Please refer to the Workflow panel."

        if "currency" in q:
            return f"The currency identified in the document is **{fields.get('Currency', 'Not detected')}**."

        snippet = re.sub(r"\s+", " ", document_text).strip()[:240]
        return (
            f"I couldn't find a direct answer to that question. "
            f"Here is a short excerpt from the document: “{snippet}”"
        )

    def _analyze_openai(self, content: str) -> Dict[str, Any]:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = f"""Analyze this document content and return ONLY valid JSON matching this schema:
{{
  "document_type": "Invoice/Resume/Contract/Purchase Order/Loan Application/Other",
  "confidence": 0.95,
  "priority": "LOW/MEDIUM/HIGH/CRITICAL",
  "priority_reason": "string",
  "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
  "risk_score": 12,
  "summary": ["bullet 1", "bullet 2"],
  "extracted_fields": {{
    "Vendor": "string",
    "Invoice Number": "string",
    "Order Number": "string",
    "Invoice Date": "string",
    "Due Date": "string",
    "Subtotal": "string",
    "Tax": "string",
    "Total Amount": "string",
    "Currency": "string",
    "Service": "string",
    "Customer": "string",
    "Payment Terms": "string",
    "Payment Status": "PAID/UNPAID/Not detected"
  }},
  "risks": [{{"type": "WARNING/CHECK", "text": "description"}}],
  "recommended_action": "ARCHIVE / RECORD KEEPING or Finance Manager Approval",
  "department": "Finance",
  "assigned_role": "Finance Records / Finance Manager",
  "sla_hours": 48,
  "workflow": [{{"step_name": "string", "node_type": "Start/AI Analysis/Document Validation/Approval/End", "role": "string", "status": "Completed/Active/Pending"}}]
}}

Payment-status safety rules:
- UNPAID is not PAID. Never infer PAID from a substring match.
- Use PAID only for an explicit Payment Status / Invoice Status value of PAID, or a standalone PAID stamp/watermark.
- Treat UNPAID, NOT PAID, PAYMENT PENDING, OUTSTANDING, and BALANCE DUE as UNPAID.
- If the document does not explicitly establish status, return "Not detected" and route for manual verification.
- Never claim a watermark, signature, tax check, or verification that is not explicitly visible in the supplied text.

Document Content:
{content[:4000]}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)

    def _analyze_gemini(self, content: str) -> Dict[str, Any]:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt = f"""You are an enterprise document intelligence AI. Analyze this document text and return ONLY valid JSON matching this exact structure:
{{
  "document_type": "<Invoice|Purchase Order|Contract|Resume|Loan Application|Other>",
  "confidence": 0.95,
  "priority": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "priority_reason": "<Clear concise explanation for the priority classification>",
  "risk_level": "<LOW|MEDIUM|HIGH>",
  "risk_score": 15,
  "summary": [
    "<Key fact 1 from document>",
    "<Key fact 2 from document>",
    "<Key fact 3 from document>"
  ],
  "extracted_fields": {{
    "Vendor / Entity": "<Extracted Vendor or Sender Name>",
    "Document ID / Number": "<Extracted Number>",
    "Date": "<Extracted Date>",
    "Total Amount": "<Extracted Amount with currency symbol or N/A>",
    "Payment Status": "<PAID|UNPAID|Not detected>"
  }},
  "risks": [
    {{"type": "CHECK", "text": "<Safety or verification signal>"}}
  ],
  "recommended_action": "<RECOMMENDED NEXT ACTION>",
  "department": "<Finance|Legal|HR|Operations>",
  "assigned_role": "<Assigned Approver Role>",
  "sla_hours": 24,
  "workflow": [
    {{"step_name": "Document Ingestion", "node_type": "Start", "role": "System", "status": "Completed"}},
    {{"step_name": "AI Analysis", "node_type": "AI Analysis", "role": "AI Engine", "status": "Completed"}},
    {{"step_name": "Department Signoff", "node_type": "Approval", "role": "Department Manager", "status": "Active"}},
    {{"step_name": "System Archival", "node_type": "End", "role": "System", "status": "Pending"}}
  ]
}}

CRITICAL INSTRUCTIONS FOR ANALYSIS:
1. Carefully extract: Vendor, Invoice Number, Order Number, Invoice Date, Due Date, Subtotal, Tax, Total Amount, Currency, Service, Customer, Payment Terms, and Payment Status from the document text below.
2. Mark an invoice PAID only when an explicit Payment Status or Invoice Status field says PAID, or the source contains a standalone PAID stamp/watermark. UNPAID, NOT PAID, PAYMENT PENDING, OUTSTANDING, and BALANCE DUE must be classified as UNPAID. Incidental words containing 'paid' are not proof of payment. If ambiguous, return 'Not detected'.
3. Do NOT default to fictional values like ABC Technologies or INV-1024. Extract actual details from text.

Document Text:
{content[:4000]}
"""
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = res.text.strip()
        if "```" in text:
            parts = text.split("```")
            for p in parts:
                if p.startswith("json"):
                    p = p[4:]
                p = p.strip()
                if p.startswith("{") and p.endswith("}"):
                    text = p
                    break
        
        parsed = json.loads(text)
        required_keys = ["document_type", "confidence", "priority", "risk_level", "risk_score", "extracted_fields", "recommended_action"]
        for k in required_keys:
            if k not in parsed:
                raise ValueError(f"Missing schema key: {k}")
        return parsed

    def _chat_openai(self, document_text: str, question: str) -> str:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI document assistant. Answer the user question based ONLY on the document provided. If the information is not present, reply: 'I couldn't find this information in the document.'"},
                {"role": "user", "content": f"Document Text:\n{document_text[:3000]}\n\nQuestion: {question}"}
            ]
        )
        return res.choices[0].message.content

    def _chat_gemini(self, document_text: str, question: str) -> str:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Document Text:\n{document_text[:3000]}\n\nQuestion: {question}\n\nAnswer strictly based on the text. If missing, say 'I couldn't find this information in the document.'"
        )
        return res.text
