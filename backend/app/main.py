import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env variables before other imports
load_dotenv()

from backend.app.database.session import engine, Base, SessionLocal
from backend.app.database import models, crud
from backend.app.api.endpoints import router
from backend.app.authentication.auth import get_password_hash

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize database schema automatically on startup
logger.info("Initializing relational database models...")
Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager

def seed_admin_user():
    """
    Seeds a default admin user on startup if the database is empty.
    """
    db = SessionLocal()
    try:
        admin_user = crud.get_user_by_username(db, "admin")
        if not admin_user:
            logger.info("Seeding default administrator user: username 'admin', password 'adminpassword123'...")
            hashed_pwd = get_password_hash("adminpassword123")
            crud.create_user(db, username="admin", password_hashed=hashed_pwd, role="admin")
            logger.info("Administrator user created successfully.")
    except Exception as e:
        logger.error(f"Error seeding admin user: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_admin_user()
    yield

app = FastAPI(
    title="WHMCS AI Assistant Pro API",
    description="Enterprise AI Sales & Customer Support Agent Backend Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to WHMCS AI Assistant Pro API",
        "docs_url": "/docs",
        "health_check": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=True)
