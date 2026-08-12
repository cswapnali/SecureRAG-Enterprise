# 🛡️ SecureRAG Enterprise 

SecureRAG Enterprise is an enterprise-grade Retrieval-Augmented Generation (RAG) system designed to query private corporate data securely. Features **Role-Based Access Control (RBAC)**, multi-layered **Guardrails** (PII Protection & Out-of-Scope Interception), **Cost & Token Monitoring with Budget Alerts**, and an **Integrated RAGAS Evaluation Framework**.

---

## ✨ Key Features & Capabilities 

### 📊 1. RAGAS Evaluation Framework Integration
- **RAG Triad Metrics Evaluator** (`app/services/ragas_evaluator.py`):
  - **Faithfulness**: Verifies that generated answers are strictly grounded in retrieved context without hallucination.
  - **Answer Relevancy**: Evaluates how directly the answer addresses the user's question.
  - **Context Precision**: Evaluates the signal-to-noise ratio of retrieved context chunks.
- **Ragas Continuous Evaluation Suite** (`evals/run_evals.py`):
  - Automatically calculates overall Ragas scores alongside security & RBAC pass rates.
  - Outputs evaluation report metrics to `evals/eval_report.json`.
- **Ragas UI Dashboard**:
  - Displays real-time Ragas metric cards (Faithfulness, Answer Relevancy, Context Precision) in the Streamlit Portal (**📊 Continuous Evals & Monitoring** tab).

### 🔐 2. Role-Based Access Control (RBAC)
- **Departmental Isolation**: Users in `finance`, `hr`, `marketing`, and `engineering` roles can only search knowledge bases corresponding to their security clearance level.
- **👑 C-Level Executive Access**: Users with the `c_level` role (e.g. `Nick`) bypass role filters and obtain full search access across all corporate data repositories.
- **Vector Filter Enforcement**: ChromaDB similarity queries dynamically apply `{"role": {"$in": allowed_roles}}` metadata filters at the retrieval layer.

### 🛡️ 3. Guardrails Subsystem
- **🔒 PII Detection & Sanitization**:
  - Automatically scans prompts and model outputs for sensitive data including Email addresses, Phone numbers, Social Security Numbers (SSN), Credit Card numbers, and API keys.
  - Replaces sensitive strings with redacted tags (e.g., `[EMAIL_REDACTED]`, `[SSN_REDACTED]`).
- **🚫 Out-of-Scope Question Interception**:
  - Detects non-enterprise questions (recipes, trivia, sports, general entertainment, or illegal tasks) before hitting ChromaDB or Groq LLM.
  - Returns an immediate refusal warning to prevent token wastage and policy violations.

### 💰 4. Real-Time Cost & Token Monitoring
- **Token Counter**: Measures `prompt_tokens`, `completion_tokens`, and `total_tokens` per request.
- **USD Cost Engine**: Calculates cost based on Groq Llama 3.3 70B rates ($0.59 / 1M prompt tokens, $0.79 / 1M output tokens).
- **Budget Threshold Alerts**: Triggers visual warning banners in the UI and log alerts when total spend breaches configured threshold limits ($0.005 USD demo limit).
- **Persistent Log Store**: Saves historical metric logs in `app/data/cost_metrics.json`.

---

## 🔑 Demo Test Credentials

| Username | Password | Role | Security Clearance / Permissions |
| :--- | :--- | :--- | :--- |
| **Nick** | `execpass123` | `c_level` | 👑 **C-Level Executive**: Full access to ALL department knowledge bases |
| **Sam** | `financepass` | `finance` | 💰 **Finance**: Financial reports, quarterly summaries |
| **Natasha** | `hrpass123` | `hr` | 👥 **HR**: Employee policies, payroll, employee directory |
| **Tony** | `password123` | `engineering` | 🔧 **Engineering**: System architecture, codebase docs |
| **Bruce** | `securepass` | `marketing` | 📢 **Marketing**: Marketing campaigns, budget breakdown |

---

## 📁 Project Directory Structure

```text
SecureRAG_Enterprise/
├── app/
│   ├── data/
│   │   └── cost_metrics.json      # Persistent token cost & usage storage
│   ├── services/
│   │   ├── cost_tracker.py        # Token counting, cost calculation & alerts
│   │   ├── guardrails.py          # PII sanitization & out-of-scope classifier
│   │   ├── query_embedding.py     # ChromaDB similarity search with RBAC filter
│   │   └── ragas_evaluator.py     # Ragas Triad metrics evaluator (Faithfulness, Relevancy, Precision)
│   ├── utils/
│   │   └── md_chromadb.py         # Markdown/CSV document chunking & vector indexing
│   └── main.py                    # FastAPI server entrypoint
├── evals/
│   ├── eval_dataset.json          # Evaluation benchmark test dataset with ground truths
│   ├── eval_report.json           # Latest continuous evaluation report output (includes Ragas scores)
│   └── run_evals.py               # Ragas & RBAC automated evaluation test runner script
├── resources/
│   └── data/                      # Private corporate documents structured by role
│       ├── engineering/
│       ├── finance/
│       ├── general/
│       ├── hr/
│       └── marketing/
├── chroma_db/                     # Persistent Chroma vector database
├── streamlit_app.py               # Streamlit Portal with Chat, Cost Dashboard & Ragas Evals
└── pyproject.toml                 # Project metadata and dependencies
```

---

## 🚀 How to Run 

### 1. Start FastAPI Backend
```powershell
cd "SecureRAG_Enterprise"
venv\Scripts\python.exe app/main.py
```

### 2. Launch Streamlit Web UI
```powershell
cd "SecureRAG_Enterprise"
venv\Scripts\streamlit.exe run streamlit_app.py
```

### 3. Run Ragas Evaluation Suite
```powershell
venv\Scripts\python.exe evals/run_evals.py
```
*Executes Ragas Faithfulness, Answer Relevancy, and Context Precision metrics evaluation and updates `evals/eval_report.json`.*
