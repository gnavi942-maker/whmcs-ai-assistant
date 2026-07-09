from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="admin") # admin, operator
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    price_text = Column(String(100))
    price_numeric = Column(Float, default=0.0)
    short_description = Column(Text)
    full_description = Column(Text)
    categories = Column(JSON, default=list) # List of category strings
    tags = Column(JSON, default=list)       # List of tags strings
    compatibility = Column(JSON, default=list) # Compatibility details
    features = Column(JSON, default=list)    # Bulleted features list
    images = Column(JSON, default=list)      # Image URL list
    url = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(100), default="document") # product_doc, guide, blog, faq
    url = Column(String(255), unique=True, nullable=False)
    categories = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    business_type = Column(String(100))
    requirement = Column(Text)
    status = Column(String(50), default="new") # new, contacted, won, lost
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    role = Column(String(50), nullable=False) # user, assistant
    content = Column(Text, nullable=False)
    user_feedback = Column(String(50)) # positive, negative, None
    created_at = Column(DateTime, default=datetime.utcnow)

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True)
    event_type = Column(String(100), nullable=False) # query, failed_query, lead_gen, click_recommendation
    query_text = Column(Text)
    response_text = Column(Text)
    matched_products = Column(JSON, default=list) # Recommended products list
    rating = Column(Integer) # Optional query rating 1-5
    created_at = Column(DateTime, default=datetime.utcnow)
