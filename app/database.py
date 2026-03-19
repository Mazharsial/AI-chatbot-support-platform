from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
import datetime
from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # required for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─────────────────────────────────────────────────────────────
# Database Models
# ─────────────────────────────────────────────────────────────

class Customer(Base):
    """One row per unique user (telegram user or website visitor)."""
    __tablename__ = "customers"

    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id    = Column(String, unique=True, nullable=True, index=True)
    name           = Column(String(100), nullable=True)
    channel        = Column(String(20), default="telegram")   # telegram / web
    total_messages = Column(String, default="0")
    first_seen     = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen      = Column(DateTime, default=datetime.datetime.utcnow)


class Conversation(Base):
    """Every single message exchanged — user message + bot reply."""
    __tablename__ = "conversations"

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=True)
    user_id     = Column(String, index=True)   # telegram user id or browser session id
    channel     = Column(String(20))           # telegram / web
    message     = Column(Text)                 # what the user sent
    reply       = Column(Text)                 # what the bot replied
    intent      = Column(String(50))           # classified intent label
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)


class Ticket(Base):
    """Auto-created for complaints, refund requests, and human handoff requests."""
    __tablename__ = "tickets"

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id     = Column(String, index=True)
    channel     = Column(String(20))
    intent      = Column(String(50))
    message     = Column(Text)                 # the message that triggered the ticket
    status      = Column(String(20), default="open")   # open / resolved / escalated
    assigned_to = Column(String(100), nullable=True)   # human agent name or email
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class FAQEntry(Base):
    """FAQ question-answer pairs. Searched via ChromaDB in Phase 3."""
    __tablename__ = "faq_entries"

    id       = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(Text)
    answer   = Column(Text)
    category = Column(String(50), default="general")
    active   = Column(Boolean, default=True)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def get_db():
    """FastAPI dependency — yields a DB session, always closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once on app startup."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
