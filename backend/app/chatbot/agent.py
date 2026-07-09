import os
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

# LangChain Imports
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
try:
    from langchain_community.chat_models.ollama import ChatOllama
except ImportError:
    try:
        from langchain_community.chat_models import ChatOllama
    except ImportError:
        ChatOllama = None

from backend.app.rag.vector_store import query_vector_db
from backend.app.database import crud

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are "WHMCS AI Assistant Pro", a premium Enterprise AI Sales Assistant and Customer Support Agent for "WHMCS Modules" (https://whmcsmodules.org/).

Your core capabilities:
1. Product Recommendation: Help visitors discover, compare, and buy WHMCS modules. Explain features, compatibility, and pricing.
2. Support Assistant: Troubleshoot setup, licensing, installation, and module configuration queries.
3. Website Navigation: Guide users directly to pages. Output clickable button actions in brackets, e.g. `[Open Modexa WHMCS Theme](https://whmcsmodules.org/product/modexa-whmcs-theme/)`.
4. Lead Capture: If the user asks for a customized module, custom quote, enterprise deployment, or requests human transfer, politely ask for their Name, Email, Business Type, and Requirement.
5. Human Support Transfer: If the user is frustrated, has a complex configuration problem, or explicitly asks for a human, indicate that you are transferring them to a live support ticket.

Important Guidelines:
- Language Support: Detect and respond in the user's language (supporting English, Hindi (हिंदी), Punjabi (ਪੰਜਾਬੀ), and Arabic (العربية) natively).
- Keep replies concise, helpful, and formatted in Markdown.
- Always include direct product links when recommending modules.
- Use the relevant database context provided to you. Do NOT make up product names, prices, or documentation details.
- Never output TODO comments or placeholder information.
"""

def get_llm():
    """
    Initializes and returns the configured LLM provider.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    model_name = os.getenv("MODEL_NAME", "gemini-1.5-flash")

    logger.info(f"Initializing LLM Provider: {provider} (Model: {model_name})")

    if provider == "openai":
        return ChatOpenAI(
            model=model_name,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3
        )
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.3
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model=model_name,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3
        )
    elif provider == "ollama":
        if ChatOllama is None:
            raise ValueError("Ollama client library is not available. Please install 'langchain-ollama' to run local Ollama models.")
        return ChatOllama(
            model=model_name,
            temperature=0.3
        )
    else:
        # Fallback to a mock/simple OpenAI local or raise configuration error
        logger.warning(f"Unknown LLM provider {provider}, falling back to Mock/OpenAI wrapper")
        return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

def check_for_lead_generation(message: str) -> bool:
    """
    Heuristic check to determine if the message requires capturing lead information.
    """
    keywords = ["custom development", "enterprise", "pricing quote", "custom module", "contact human", "talk to human", "live agent", "support agent", "hire", "consultation"]
    return any(kw in message.lower() for kw in keywords)

def run_agent(db: Session, session_id: str, user_query: str) -> Tuple[str, List[str]]:
    """
    Main orchestration function:
    1. Queries the Vector DB for matching context.
    2. Fetches chat history from DB/Redis.
    3. Builds the System Prompt, Context, and History.
    4. Invokes the LLM to get a response.
    5. Saves chat history.
    6. Logs analytics events.
    """
    # 1. Fetch relevant vector database context
    search_results = query_vector_db(user_query, n_results=4)
    
    context_str = "\n\n--- RELEVANT WEBSITE KNOWLEDGE CONTEXT ---\n"
    matched_products = []
    
    for idx, res in enumerate(search_results):
        meta = res["metadata"]
        title = meta.get("title", "Unknown")
        url = meta.get("url", "")
        m_type = meta.get("type", "document")
        
        context_str += f"\n[{idx+1}] Source: {title} ({url})\nContent: {res['text']}\n"
        
        if m_type == "product" and title not in matched_products:
            matched_products.append(title)
            
    # 2. Fetch User Long-Term Memory
    from backend.app.chatbot.memory import get_long_term_memory
    lt_memory = get_long_term_memory(db, session_id)

    # 3. Get past Chat History (Short-term memory)
    history_records = crud.get_chat_history(db, session_id=session_id, limit=8)
    messages = [SystemMessage(content=SYSTEM_PROMPT + context_str + lt_memory)]
    
    for record in history_records:
        if record.role == "user":
            messages.append(HumanMessage(content=record.content))
        else:
            messages.append(AIMessage(content=record.content))
            
    # Add the current query
    messages.append(HumanMessage(content=user_query))
    
    # 3. Call LLM
    try:
        llm = get_llm()
        response = llm.invoke(messages)
        response_text = response.content
    except Exception as e:
        logger.error(f"Error invoking LLM model: {e}")
        # Check if we have RAG search results to generate a rule-based fallback response
        if search_results:
            response_text = "Here is what I found in our database matching your request:\n\n"
            for idx, res in enumerate(search_results):
                meta = res["metadata"]
                title = meta.get("title", "Module")
                url = meta.get("url", "#")
                # Clean clean description
                desc = res['text'][:250].strip().replace('\n', ' ') + "..."
                price = meta.get("price_text", "")
                price_str = f" (**Price**: {price})" if price else ""
                
                response_text += f"- **[{title}]({url})**{price_str}\n  {desc}\n\n"
            response_text += "*(Note: Since the AI model API key is not fully configured in the `.env` file, I am displaying these database matches directly)*"
        else:
            # Graceful fallback response
            response_text = "I'm having trouble connecting to my brain right now. Please check back in a moment! You can also contact us directly at support@whmcsmodules.org."

    # 4. Check if query was unresolved/failed (relevance score threshold or keyword check)
    event_type = "query"
    if len(search_results) == 0 or (search_results and search_results[0]["relevance_score"] < 0.2):
        # Mark as failed/unresolved query if RAG confidence is low
        event_type = "failed_query"
        
    # If user query triggers lead generation keyword
    if check_for_lead_generation(user_query):
        event_type = "lead_gen"

    # 5. Persist the interaction
    crud.add_chat_message(db, session_id=session_id, role="user", content=user_query)
    crud.add_chat_message(db, session_id=session_id, role="assistant", content=response_text)
    crud.log_analytics_event(db, session_id=session_id, event_type=event_type, query_text=user_query, response_text=response_text, matched_products=matched_products)
    
    return response_text, matched_products
