import sys
from pathlib import Path
from typing import Dict, Any

root_dir = Path(__file__).parent.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
app_dir = Path(__file__).parent.resolve()
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os
from dotenv import load_dotenv

from app.services.guardrails import apply_guardrails, sanitize_pii
from app.services.cost_tracker import record_usage, get_cost_summary, reset_cost_metrics

load_dotenv()

app = FastAPI(title="SecureRAG Enterprise API with RBAC, Guardrails & Cost Monitoring")
security = HTTPBasic()

users_db: Dict[str, Dict[str, str]] = {
    "Tony": {"password": "password123", "role": "engineering"},
    "Bruce": {"password": "securepass", "role": "marketing"},
    "Sam": {"password": "financepass", "role": "finance"},
    "Peter": {"password": "pete123", "role": "engineering"},
    "Sid": {"password": "sidpass123", "role": "marketing"},
    "Natasha": {"password": "hrpass123", "role": "hr"},
    "Nick": {"password": "execpass123", "role": "c_level"}  # C-Level Executive with full access
}

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password
    user = users_db.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    passwd = user.get("password") or user.get("passwoed")
    if passwd != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    return {"username": username, "role": user["role"]}

@app.get("/login")
def login(user=Depends(authenticate)):
    return {"message": f"Welcome {user['username']}!", "role": user["role"]}

@app.get("/test")
def test(user=Depends(authenticate)):
    return {"message": f"Hello {user['username']}! You can now chat.", "role": user["role"]}

@app.get("/cost-metrics")
def cost_metrics():
    """Retrieve cost summary and token usage metrics."""
    return get_cost_summary()

@app.post("/reset-cost")
def reset_cost():
    """Reset cost tracking stats."""
    return reset_cost_metrics()

@app.post("/chat")
def query(user=Depends(authenticate), message: str = "Hello"):
    from app.services.query_embedding import query_embedding
    from groq import Groq

    # 1. APPLY GUARDRAILS (PII + Out-of-Scope Detection)
    guardrail_result = apply_guardrails(message)
    
    # Block out-of-scope requests before hitting retrieval or LLM
    if guardrail_result["is_out_of_scope"]:
        return {
            "answer": "⚠️ Out-of-Scope Warning: This query is out of scope for the internal enterprise corporate assistant. Please ask questions related to company operations, HR policies, financial summaries, marketing expenses, or engineering systems.",
            "sources": [],
            "guardrails": guardrail_result,
            "cost_metrics": {
                "query_cost_usd": 0.0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cumulative_cost_usd": get_cost_summary()["total_cost_usd"],
                "alert_triggered": get_cost_summary()["alert_triggered"]
            }
        }

    clean_message = guardrail_result["sanitized_prompt"]

    # 2. RETRIEVAL (Filtered by User RBAC Role)
    retrieved_documents = query_embedding(clean_message, user_role=user["role"])
    
    context_blocks = []
    for doc in retrieved_documents:
        source_name = Path(doc.metadata.get("source", "Unknown")).name
        role_label = doc.metadata.get("role", "general")
        context_blocks.append(f"Source: {source_name} (Access Role: {role_label})\nContent: {doc.page_content}")
    
    context_str = "\n\n".join(context_blocks)
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
    You are a helpful internal corporate assistant. Answer the user's question using ONLY the provided context.
    If the answer is not present in the context, respond exactly with: "I don't have enough information."
    
    User Role: {user['role']}
    
    Context:
    {context_str}

    Question:
    {clean_message}
    """

    # 3. LLM GENERATION
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Answer questions only from the provided context. If the answer is not present, respond exactly with: I don't have enough information."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    raw_answer = response.choices[0].message.content
    
    # Sanitize LLM response output for PII leakage protection
    sanitized_answer, _, _ = sanitize_pii(raw_answer)

    # 4. TRACK TOKEN USAGE & COST METRICS
    usage = getattr(response, "usage", None)
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    
    cost_info = record_usage(
        username=user["username"],
        role=user["role"],
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens
    )

    print(f"User: {user['username']} ({user['role']}) | Cost: ${cost_info['query_cost_usd']} | Tokens: {cost_info['total_tokens']}")

    return {
        "answer": sanitized_answer,
        "sources": [
            {
                "source": Path(doc.metadata.get("source", "Unknown")).name,
                "role": doc.metadata.get("role", "general")
            } for doc in retrieved_documents
        ],
        "guardrails": guardrail_result,
        "cost_metrics": cost_info
    }

if __name__ == "__main__":
    import uvicorn
    from app.utils.md_chromadb import embedding_func

    print("Running embedding indexer...")
    embedding_func()
    print("Starting FastAPI Server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)