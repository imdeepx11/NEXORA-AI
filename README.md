<p align="center">
  <img src="https://img.shields.io/badge/NEXORA_AI-Intelligent_Documents-00A859?style=for-the-badge&logo=data:image/svg+xml;base64,..." alt="NEXORA AI" />
</p>

<h1 align="center">NEXORA AI</h1>
<p align="center"><strong>Intelligent Documents. Smarter Workflows.</strong></p>
<p align="center">AI-powered document intelligence and workflow automation for modern enterprises.</p>

<p align="center">
  <a href="https://nexora-ai-c130d.web.app/"><strong>🔥 Firebase Hosting</strong></a> •
  <a href="https://nexora-ai-imdeepx11.vercel.app/"><strong>✨ Vercel</strong></a> •
  <a href="https://nexora-backend-30jt.onrender.com/docs"><strong>🌐 Live API & Swagger Docs</strong></a> •
  <a href="https://github.com/imdeepx11/Nexora-AI"><strong>📦 GitHub Repository</strong></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.141-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-4.3-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-8.3-646CFF?style=flat-square&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
</p>

---

## 🚀 Live Cloud Deployment Links

- **Frontend (Firebase Hosting)**: [https://nexora-ai-c130d.web.app/](https://nexora-ai-c130d.web.app/)
- **Frontend (Vercel)**: [https://nexora-ai-imdeepx11.vercel.app/](https://nexora-ai-imdeepx11.vercel.app/)
- **Backend API (Render)**: [https://nexora-backend-30jt.onrender.com](https://nexora-backend-30jt.onrender.com)
- **FastAPI Interactive Docs**: [https://nexora-backend-30jt.onrender.com/docs](https://nexora-backend-30jt.onrender.com/docs)


---

## Overview

**NEXORA AI** is an enterprise-grade web application that demonstrates end-to-end **Intelligent Document Processing (IDP)**, **Business Process Management (BPM)**, and **AI-Assisted Decision Support**.

Upload any business document — invoice, contract, purchase order, or resume — and watch the AI pipeline classify it, extract structured data, assess risk, assign priority, recommend an action, and route it through an automated approval workflow with full audit trail.

### Workspace Isolation

NEXORA AI now uses tenant-scoped persistence. A verified Firebase identity is mapped to a backend user and an isolated organization/workspace. All document reads and writes are filtered by that workspace, and related workflows, analytics, audit logs, AI document chat, and workspace configuration use the same tenant boundary. Uploaded files are no longer exposed through a public static `/uploads` route; file access requires an authenticated request for a document in the current workspace.

```
PDF / DOCX / TXT Upload
        ↓
AI Content Extraction & Classification
        ↓
Structured Field Extraction (vendor, amount, dates, terms)
        ↓
Risk Assessment (0–100 score + flags)
        ↓
SLA Priority Detection & AI Recommended Action
        ↓
Automated Workflow Routing & Human Approval
        ↓
Immutable Audit Log & Analytics Dashboard
```

---

## Features

| Category | Details |
|---|---|
| **AI Document Analysis** | PDF text extraction via PyMuPDF, document classification with confidence scores, structured field extraction, risk scoring, priority detection, and AI-recommended actions |
| **Grounded QA Chat** | Ask natural-language questions about any uploaded document — answers are grounded in the actual extracted text |
| **Workflow Automation** | Rule-based workflow routing with configurable nodes (AI Analysis → Validation → Approval → Notification → Assignment) |
| **Approval System** | Multi-role decision modal (Approve / Reject / Request Changes) with audit comment trails |
| **Analytics Dashboard** | Executive KPIs, 30-day document volume trends, automation rates, SLA compliance, and process bottleneck detection |
| **Audit Logs** | Immutable compliance event stream with filtering by action type, user, and timestamp |
| **AI Providers** | Built-in demo mode (no API key required), Google Gemini, and OpenAI GPT-4o support |
| **Enterprise UI** | Clean white + emerald green theme, responsive layout, Lucide icons, Recharts visualizations |
| **Multi-Tenant Workspaces** | Every verified Firebase account receives an isolated workspace; documents, workflows, analytics, audit logs, AI document access, and workspace settings are scoped to that tenant |
| **Protected File Storage** | Uploaded files are stored under tenant-specific directories and are only served through authenticated, tenant-scoped API access |

---

## Tech Stack.

```
┌─────────────────────────────────────────────────────────┐
│  Frontend                                               │
│  React 19 · Vite 8 · Tailwind CSS 4 · Lucide · Recharts│
└────────────────────────┬────────────────────────────────┘
                         │ REST API (proxy via Vite)
┌────────────────────────▼────────────────────────────────┐
│  Backend                                                │
│  Python 3.12 · FastAPI · Uvicorn · SQLAlchemy · Pydantic│
│  PyMuPDF · python-docx · Google GenAI · OpenAI SDK      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  Database: SQLite (auto-seeded with demo data)          │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
NEXORA-AI/
├── main.py                  # Root entry point — starts the backend
├── requirements.txt         # Python dependencies
├── render.yaml              # Render zero-config blueprint
├── .env.example             # Environment variable template
├── .gitignore
├── README.md
│
├── backend/
│   ├── main.py              # Cloud production entrypoint
│   ├── requirements.txt     # Backend dependencies
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── api/             # REST endpoint routers
│   │   ├── database/        # Database models & seeding
│   │   └── services/        # AI Service & Document Extractor
│   └── uploads/             # User-uploaded files (gitignored)
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── vercel.json          # Vercel deployment configuration
    ├── index.html
    └── src/
        ├── App.jsx
        ├── api.js           # API client
        ├── components/
        └── pages/
```

---

## Quick Start (Local Development)

> **Important:** The `localhost` links below are local development addresses. They work only on the same computer where you have started the backend and frontend servers. Opening these links directly from GitHub will not start the application.

### Prerequisites

- **Python** 3.10+
- **Node.js** 20.19+ or 22.12+ and npm (required by the Vite 8 frontend)

Check your installed versions before setup:

```bash
python --version
node --version
npm --version
```

### 1. Clone the repository

```bash
git clone https://github.com/imdeepx11/NEXORA-AI.git
cd NEXORA-AI
```

### 2. Set up and start the backend

Open **Terminal 1** in the repository root:

```bash
python -m venv venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.\\venv\\Scripts\\Activate.ps1
```

```bash
# macOS / Linux
source venv/bin/activate
```

Install the backend dependencies and start the server:

```bash
pip install -r requirements.txt
python main.py
```

**Keep Terminal 1 open.** When the backend is running, these local endpoints are available on your computer:

- API health check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) — expected response: `{"status":"ok"}`
- Swagger API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Set up and start the frontend

Open **Terminal 2** in the repository root:

```bash
cd frontend
npm install
npm run dev
```

Keep Terminal 2 open as well. Vite prints the local address when it starts. Open the address shown in that terminal, normally:

[http://localhost:5173](http://localhost:5173)

If port 5173 is already in use, Vite may select another port (for example, 5174). Use the exact address printed in the terminal.

### Local Development Troubleshooting

- **The browser says “localhost refused to connect”:** the relevant server is not running, has stopped, or is using a different port. Start the backend and frontend in two separate terminals.
- **The frontend starts but API calls fail:** confirm the backend health check above returns `{"status":"ok"}`, and keep `VITE_API_BASE_URL=/api` in `frontend/.env` if you created that file from `.env.example`. The Vite development proxy forwards `/api` requests to the local backend.
- **Vite reports an unsupported Node.js version:** install Node.js 20.19+ or 22.12+, then reopen the terminal and run `npm install` again.

## Walkthrough

1. **Register / Sign in** → Use a verified Firebase email account or Google sign-in
2. **Dashboard** → Show workspace-scoped KPIs and recent documents
3. **Documents** → Browse only documents belonging to the signed-in workspace
4. **Upload** → Upload a sample PDF invoice into the current workspace
5. **AI Analyzer** → Click "Analyze with AI" and walk through:
   - Document classification with confidence score
   - Extracted fields (vendor, invoice number, amounts, dates, payment status)
   - Risk assessment score and flags
   - AI recommended action
   - Grounded QA chat ("What is the total amount?", "When is the due date?")
6. **Approval** → Submit an approval decision with comments
7. **Workflows** → Observe the workflow timeline update
8. **Analytics** → Show process intelligence and bottleneck insights
9. **Audit Logs** → Demonstrate the workspace-scoped compliance trail

---

## License

MIT License — NEXORA AI © 2026

---

<p align="center">
  Built by <strong>Deepak Gupta</strong>
</p>
