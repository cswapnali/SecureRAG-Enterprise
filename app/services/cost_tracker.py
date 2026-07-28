import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
COST_FILE = DATA_DIR / "cost_metrics.json"

PROMPT_TOKEN_RATE = 0.59 / 1_000_000
COMPLETION_TOKEN_RATE = 0.79 / 1_000_000

DEFAULT_COST_ALERT_THRESHOLD = 0.005  

def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not COST_FILE.exists():
        initial_data = {
            "total_queries": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "alert_threshold_usd": DEFAULT_COST_ALERT_THRESHOLD,
            "alert_triggered": False,
            "query_history": []
        }
        with open(COST_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=2)

def calculate_query_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Calculates USD cost for a single LLM request."""
    prompt_cost = prompt_tokens * PROMPT_TOKEN_RATE
    completion_cost = completion_tokens * COMPLETION_TOKEN_RATE
    return prompt_cost + completion_cost

def record_usage(username: str, role: str, prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
    """
    Records token usage and cost for a query, updates persistent json store,
    and returns metrics with alert status.
    """
    _ensure_data_dir()
    
    total_tokens = prompt_tokens + completion_tokens
    query_cost = calculate_query_cost(prompt_tokens, completion_tokens)
    
    with open(COST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data["total_queries"] += 1
    data["total_prompt_tokens"] += prompt_tokens
    data["total_completion_tokens"] += completion_tokens
    data["total_tokens"] += total_tokens
    data["total_cost_usd"] = round(data["total_cost_usd"] + query_cost, 6)
    
    # Check alert threshold
    if data["total_cost_usd"] >= data.get("alert_threshold_usd", DEFAULT_COST_ALERT_THRESHOLD):
        data["alert_triggered"] = True
        
    query_record = {
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "role": role,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": round(query_cost, 6)
    }
    
    # Keep last 50 queries in history
    data["query_history"].append(query_record)
    if len(data["query_history"]) > 50:
        data["query_history"] = data["query_history"][-50:]
        
    with open(COST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    return {
        "query_cost_usd": round(query_cost, 6),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cumulative_cost_usd": data["total_cost_usd"],
        "alert_triggered": data["alert_triggered"],
        "alert_threshold_usd": data.get("alert_threshold_usd", DEFAULT_COST_ALERT_THRESHOLD)
    }

def get_cost_summary() -> Dict[str, Any]:
    """Retrieves current cost summary and usage history."""
    _ensure_data_dir()
    with open(COST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def reset_cost_metrics() -> Dict[str, Any]:
    """Resets tracking counters."""
    _ensure_data_dir()
    reset_data = {
        "total_queries": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "alert_threshold_usd": DEFAULT_COST_ALERT_THRESHOLD,
        "alert_triggered": False,
        "query_history": []
    }
    with open(COST_FILE, "w", encoding="utf-8") as f:
        json.dump(reset_data, f, indent=2)
    return reset_data
