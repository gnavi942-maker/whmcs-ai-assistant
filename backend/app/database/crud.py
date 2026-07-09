from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.app.database.models import User, Product, Document, Lead, ChatHistory, Analytics
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- User Management ---
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password_hashed: str, role: str = "admin"):
    db_user = User(username=username, hashed_password=password_hashed, role=role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Product Management ---
def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    return db.query(Product).offset(skip).limit(limit).all()

def get_product_by_id(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def get_product_by_url(db: Session, url: str):
    return db.query(Product).filter(Product.url == url).first()

# --- Lead Management ---
def create_lead(db: Session, name: str, email: str, business_type: str = None, requirement: str = None):
    db_lead = Lead(name=name, email=email, business_type=business_type, requirement=requirement)
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

def get_leads(db: Session, skip: int = 0, limit: int = 100) -> List[Lead]:
    return db.query(Lead).order_by(desc(Lead.created_at)).offset(skip).limit(limit).all()

# --- Chat History & Sessions ---
def add_chat_message(db: Session, session_id: str, role: str, content: str):
    db_chat = ChatHistory(session_id=session_id, role=role, content=content)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def get_chat_history(db: Session, session_id: str, limit: int = 20) -> List[ChatHistory]:
    return db.query(ChatHistory).filter(ChatHistory.session_id == session_id).order_by(ChatHistory.created_at).limit(limit).all()

# --- Analytics System ---
def log_analytics_event(db: Session, session_id: str, event_type: str, query_text: str = None, response_text: str = None, matched_products: List[str] = None):
    db_analytics = Analytics(
        session_id=session_id,
        event_type=event_type,
        query_text=query_text,
        response_text=response_text,
        matched_products=matched_products or []
    )
    db.add(db_analytics)
    db.commit()
    return db_analytics

def get_dashboard_analytics(db: Session) -> Dict[str, Any]:
    """
    Fetches aggregate metrics for the dashboard.
    """
    total_conversations = db.query(func.count(func.distinct(ChatHistory.session_id))).scalar() or 0
    total_leads = db.query(func.count(Lead.id)).scalar() or 0
    total_queries = db.query(func.count(Analytics.id)).filter(Analytics.event_type == "query").scalar() or 0
    failed_queries = db.query(func.count(Analytics.id)).filter(Analytics.event_type == "failed_query").scalar() or 0
    
    # Query breakdown by day (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_stats_query = (
        db.query(
            func.date(Analytics.created_at).label("day"),
            func.count(Analytics.id).label("count")
        )
        .filter(Analytics.created_at >= seven_days_ago)
        .group_by(func.date(Analytics.created_at))
        .all()
    )
    daily_analytics = [{"date": str(stat.day), "queries": stat.count} for stat in daily_stats_query]

    # Most queried/recommended products
    # We load all analytics events and parse recommendations
    recs = db.query(Analytics.matched_products).filter(Analytics.event_type == "query").all()
    prod_counts = {}
    for r in recs:
        for p in (r.matched_products or []):
            prod_counts[p] = prod_counts.get(p, 0) + 1
            
    sorted_prods = sorted(prod_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    top_products = [{"name": name, "count": count} for name, count in sorted_prods]

    # Failed queries list
    failed_queries_list = (
        db.query(Analytics.query_text, Analytics.created_at)
        .filter(Analytics.event_type == "failed_query")
        .order_by(desc(Analytics.created_at))
        .limit(10)
        .all()
    )
    failed_queries_data = [{"query": f[0], "date": f[1].isoformat()} for f in failed_queries_list]

    return {
        "total_conversations": total_conversations,
        "total_leads": total_leads,
        "total_queries": total_queries,
        "failed_queries_count": failed_queries,
        "daily_analytics": daily_analytics,
        "top_products": top_products,
        "failed_queries": failed_queries_data
    }

# --- Data Sync Pipeline ---
def sync_scraped_data_to_db(db: Session, scraped_items: List[Dict]):
    """
    Takes crawled product and article dicts, inserting or updating the local SQLite/PostgreSQL store.
    """
    for item in scraped_items:
        url = item.get("url")
        if not url:
            continue
            
        item_type = item.get("type", "document")
        
        if item_type == "product":
            # Sync product
            db_product = db.query(Product).filter(Product.url == url).first()
            if db_product:
                # Update
                db_product.title = item.get("title", db_product.title)
                db_product.price_text = item.get("price_text", db_product.price_text)
                db_product.price_numeric = item.get("price_numeric", db_product.price_numeric)
                db_product.short_description = item.get("short_description", db_product.short_description)
                db_product.full_description = item.get("full_description", db_product.full_description)
                db_product.categories = item.get("categories", db_product.categories)
                db_product.tags = item.get("tags", db_product.tags)
                db_product.compatibility = item.get("compatibility", db_product.compatibility)
                db_product.features = item.get("features", db_product.features)
                db_product.images = item.get("images", db_product.images)
                db_product.updated_at = datetime.utcnow()
            else:
                # Insert
                db_product = Product(
                    title=item.get("title"),
                    price_text=item.get("price_text"),
                    price_numeric=item.get("price_numeric", 0.0),
                    short_description=item.get("short_description"),
                    full_description=item.get("full_description"),
                    categories=item.get("categories", []),
                    tags=item.get("tags", []),
                    compatibility=item.get("compatibility", []),
                    features=item.get("features", []),
                    images=item.get("images", []),
                    url=url
                )
                db.add(db_product)
        else:
            # Sync document/article
            db_doc = db.query(Document).filter(Document.url == url).first()
            if db_doc:
                db_doc.title = item.get("title", db_doc.title)
                db_doc.content = item.get("content", db_doc.content)
                db_doc.categories = item.get("categories", db_doc.categories)
                db_doc.tags = item.get("tags", db_doc.tags)
                db_doc.type = "blog" if "/blog/" in url or "guide" in url else "document"
                db_doc.updated_at = datetime.utcnow()
            else:
                db_doc = Document(
                    title=item.get("title"),
                    content=item.get("content"),
                    url=url,
                    categories=item.get("categories", []),
                    tags=item.get("tags", []),
                    type="blog" if "/blog/" in url or "guide" in url else "document"
                )
                db.add(db_doc)
                
    db.commit()
