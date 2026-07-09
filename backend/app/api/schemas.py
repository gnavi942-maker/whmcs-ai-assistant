from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# Auth schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Chat schemas
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    matched_products: List[str]

# Search schemas
class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 4

class SearchResultItem(BaseModel):
    text: str
    metadata: Dict[str, Any]
    relevance_score: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]

# Recommendation schemas
class RecommendRequest(BaseModel):
    requirement: str
    category: Optional[str] = None

class ProductRecommendation(BaseModel):
    id: int
    title: str
    price_text: str
    price_numeric: float
    short_description: str
    url: str
    categories: List[str]
    features: List[str]
    images: List[str]

class RecommendResponse(BaseModel):
    requirement: str
    recommendations: List[ProductRecommendation]

# Lead schemas
class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    business_type: Optional[str] = None
    requirement: Optional[str] = None

class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    business_type: Optional[str]
    requirement: Optional[str]
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

# Voice schemas
class VoiceResponse(BaseModel):
    text: str
    audio_base64: str  # Base64 encoded TTS audio
    session_id: str
