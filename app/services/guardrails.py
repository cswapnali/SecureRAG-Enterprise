import re
from typing import Dict, Any, Tuple

PII_PATTERNS = {
    "EMAIL": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),
    "PHONE": (r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE_REDACTED]'),
    "SSN": (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),
    "CREDIT_CARD": (r'\b(?:\d[ -]*?){13,16}\b', '[CREDIT_CARD_REDACTED]'),
    "API_KEY": (r'\b(?:sk-[a-zA-Z0-9]{20,T|bearer\s+[a-zA-Z0-9._-]{20,})\b', '[API_KEY_REDACTED]')
}

IN_SCOPE_KEYWORDS = [
    "employee", "payroll", "salary", "hr", "leave", "benefit", "policy",
    "financial", "finance", "revenue", "budget", "expense", "quarter", "report", "profit",
    "marketing", "campaign", "strategy", "client", "customer", "lead",
    "engineering", "architecture", "code", "tech", "infrastructure", "deployment", "system",
    "company", "corporate", "office", "team", "project", "security", "access", "application"
]

OUT_OF_SCOPE_TRIGGERS = [
    "recipe", "bake", "cook", "movie", "song", "sports", "football", "cricket", "basketball",
    "weather", "forecast", "horoscope", "astrology", "game", "gaming", "joke", "tell me a joke",
    "president of", "capital of", "who won", "lyrics", "poem", "python script to hack"
]

def sanitize_pii(text: str) -> Tuple[str, bool, list]:
    """
    Scans text for sensitive PII data and redacts it.
    Returns: (sanitized_text, contains_pii, list_of_detected_types)
    """
    sanitized = text
    detected_pii = []
    
    for pii_type, (pattern, replacement) in PII_PATTERNS.items():
        matches = re.findall(pattern, sanitized, flags=re.IGNORECASE)
        if matches:
            detected_pii.append(pii_type)
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            
    contains_pii = len(detected_pii) > 0
    return sanitized, contains_pii, detected_pii

def check_out_of_scope(text: str) -> Tuple[bool, str]:
    """
    Checks if a query is out of scope for SecureRAG Enterprise.
    Returns: (is_out_of_scope, reason)
    """
    text_lower = text.lower().strip()
    
    for trigger in OUT_OF_SCOPE_TRIGGERS:
        if trigger in text_lower:
            return True, f"Query contains out-of-scope topic: '{trigger}'"
            
    words = set(re.findall(r'\w+', text_lower))
    has_enterprise_context = any(kw in text_lower for kw in IN_SCOPE_KEYWORDS)
    
    out_of_scope_patterns = [
        r"^how do i (bake|cook|make|play|sing)\b",
        r"^(what is|who is|where is) (the capital|the weather|the score|the best movie)\b",
        r"^tell me a (joke|story|fact about space|rhyme)\b"
    ]
    
    for pat in out_of_scope_patterns:
        if re.search(pat, text_lower):
            return True, "Query matches out-of-scope generic request pattern"
            
    return False, "Query is within enterprise scope"

def apply_guardrails(prompt: str) -> Dict[str, Any]:
    """
    Main guardrail engine entrypoint.
    Executes PII redaction and Out-of-Scope detection.
    """
    sanitized_prompt, contains_pii, pii_types = sanitize_pii(prompt)
    
    is_out_of_scope, oos_reason = check_out_of_scope(prompt)
    
    return {
        "original_prompt": prompt,
        "sanitized_prompt": sanitized_prompt,
        "contains_pii": contains_pii,
        "pii_types": pii_types,
        "is_out_of_scope": is_out_of_scope,
        "out_of_scope_reason": oos_reason,
        "passed_guardrails": not is_out_of_scope
    }
