from sqlalchemy.orm import Session
from backend.app.database.models import Lead, ChatHistory, Analytics

def get_long_term_memory(db: Session, session_id: str) -> str:
    """
    Retrieves previous user profiles or captured lead details to customize
    the system prompt context (long-term preference memory).
    """
    memory_context = ""

    # 1. Check if user is associated with an existing lead
    # We look for a lead matching details from this session
    lead = db.query(Lead).order_by(Lead.created_at.desc()).first() # Simplify: get latest lead or match on email if stored
    
    # Alternatively, find previous session queries
    # Look for business type references
    history = db.query(ChatHistory).filter(
        ChatHistory.session_id == session_id
    ).order_by(ChatHistory.created_at.desc()).limit(20).all()
    
    business_type = None
    user_name = None
    
    for msg in history:
        content = msg.content.lower()
        if "my name is " in content:
            user_name = msg.content.split("my name is ")[-1].split(".")[0].strip()
        if "business type:" in content or "i run a " in content:
            business_type = content.replace("business type:", "").strip()

    if user_name or business_type:
        memory_context += "\n--- USER LONG-TERM PREFERENCES ---\n"
        if user_name:
            memory_context += f"- User Name: {user_name}\n"
        if business_type:
            memory_context += f"- Business Type/Goal: {business_type}\n"

    return memory_context
