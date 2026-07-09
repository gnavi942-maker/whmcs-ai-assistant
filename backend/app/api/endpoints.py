import io
import base64
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from gtts import gTTS
import re

# Database & Schema Imports
from backend.app.database.session import get_db
from backend.app.database import crud
from backend.app.api import schemas
from backend.app.authentication.auth import get_current_user, verify_password, get_password_hash, create_access_token
from backend.app.chatbot.agent import run_agent
from backend.app.rag.vector_store import query_vector_db
from scraper.scheduler import run_ingestion_job

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

# --- AUTHENTICATION ENDPOINTS ---
@router.post("/auth/register", response_model=schemas.Token)
def register_user(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Registers the first system administrator.
    """
    existing_user = crud.get_user_by_username(db, req.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_pwd = get_password_hash(req.password)
    user = crud.create_user(db, req.username, hashed_pwd)
    
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/auth/login", response_model=schemas.Token)
def login_user(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Dashboard user login endpoint returning JWT.
    """
    user = crud.get_user_by_username(db, req.username)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# --- CHATBOT WIDGET ENDPOINTS ---
@router.post("/chat", response_model=schemas.ChatResponse)
def chatbot_interaction(req: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    Core floating widget conversational agent routing.
    """
    response_text, matched_products = run_agent(db, req.session_id, req.message)
    return {
        "response": response_text,
        "session_id": req.session_id,
        "matched_products": matched_products
    }

@router.post("/search", response_model=schemas.SearchResponse)
def vector_search(req: schemas.SearchRequest):
    """
    Raw semantic retriever query.
    """
    results = query_vector_db(req.query, n_results=req.limit)
    formatted = []
    for r in results:
        formatted.append(schemas.SearchResultItem(
            text=r["text"],
            metadata=r["metadata"],
            relevance_score=r["relevance_score"]
        ))
    return {"query": req.query, "results": formatted}

@router.post("/recommend", response_model=schemas.RecommendResponse)
def recommend_modules(req: schemas.RecommendRequest, db: Session = Depends(get_db)):
    """
    Explicit module recommendation route using RAG and database matching.
    """
    # Quick semantic query to identify product matches
    results = query_vector_db(req.requirement, n_results=5)
    matched_ids = []
    recommendations = []
    
    for r in results:
        meta = r["metadata"]
        if meta.get("type") == "product":
            p_url = meta.get("url")
            p_record = crud.get_product_by_url(db, p_url)
            if p_record and p_record.id not in matched_ids:
                matched_ids.append(p_record.id)
                recommendations.append(schemas.ProductRecommendation(
                    id=p_record.id,
                    title=p_record.title,
                    price_text=p_record.price_text or "Contact",
                    price_numeric=p_record.price_numeric,
                    short_description=p_record.short_description or "",
                    url=p_record.url,
                    categories=p_record.categories or [],
                    features=p_record.features or [],
                    images=p_record.images or []
                ))
    
    # Fallback to general product listing if no relevant matches
    if not recommendations:
        all_prods = crud.get_products(db, limit=3)
        for p_record in all_prods:
            recommendations.append(schemas.ProductRecommendation(
                id=p_record.id,
                title=p_record.title,
                price_text=p_record.price_text or "Contact",
                price_numeric=p_record.price_numeric,
                short_description=p_record.short_description or "",
                url=p_record.url,
                categories=p_record.categories or [],
                features=p_record.features or [],
                images=p_record.images or []
            ))
            
    return {
        "requirement": req.requirement,
        "recommendations": recommendations
    }

# --- LEAD CAPTURE ENDPOINTS ---
@router.post("/lead", response_model=schemas.LeadResponse)
def capture_lead(req: schemas.LeadCreate, db: Session = Depends(get_db)):
    """
    Saves a captured lead details (Name, Email, Business, Request).
    """
    lead = crud.create_lead(
        db, 
        name=req.name, 
        email=req.email, 
        business_type=req.business_type, 
        requirement=req.requirement
    )
    return lead

@router.get("/leads", response_model=List[schemas.LeadResponse])
def fetch_all_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    """
    Dashboard protected endpoint to fetch leads.
    """
    return crud.get_leads(db, skip=skip, limit=limit)

# --- PRODUCT LISTINGS ---
@router.get("/products", response_model=List[schemas.ProductRecommendation])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves full scraped product catalog from relational database.
    """
    products = crud.get_products(db, skip=skip, limit=limit)
    res = []
    for p in products:
        res.append(schemas.ProductRecommendation(
            id=p.id,
            title=p.title,
            price_text=p.price_text or "Contact",
            price_numeric=p.price_numeric,
            short_description=p.short_description or "",
            url=p.url,
            categories=p.categories or [],
            features=p.features or [],
            images=p.images or []
        ))
    return res

# --- VOICE ASSISTANT ENDPOINTS ---
@router.post("/voice-chat", response_model=schemas.VoiceResponse)
def voice_assistant_chat(req: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    Conversational route returning text + dynamic base64 TTS synthesis audio.
    """
    response_text, _ = run_agent(db, req.session_id, req.message)
    
    # Clean text for speech synthesis (remove links, formatting)
    clean_speech_text = response_text
    clean_speech_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_speech_text) # replace [text](url) with text
    clean_speech_text = clean_speech_text.replace('*', '').replace('#', '').strip()
    
    # Generate speech audio using gTTS
    tts = gTTS(text=clean_speech_text[:500], lang='en', slow=False) # cap length to keep fast response
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    
    audio_base64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
    
    return {
        "text": response_text,
        "audio_base64": audio_base64,
        "session_id": req.session_id
    }

# --- DASHBOARD & CONTROL ENDPOINTS ---
@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    """
    Protected dashboard stats endpoint.
    """
    return crud.get_dashboard_analytics(db)

@router.post("/scrape")
def trigger_scrape(background_tasks: BackgroundTasks, current_user: Any = Depends(get_current_user)):
    """
    Protected dashboard endpoint to manually trigger scraper task asynchronously.
    """
    background_tasks.add_task(run_ingestion_job)
    return {"message": "Scraper job queued in background successfully."}

@router.get("/health")
def health_check():
    """
    Health check check for status monitoring.
    """
    return {"status": "healthy", "service": "WHMCS AI Assistant Pro Backend API"}
