"""
Analytics and ticket management endpoints for the dashboard.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db, Conversation, Ticket, Customer
import datetime

router = APIRouter()


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """Main dashboard numbers."""
    total_conversations = db.query(Conversation).count()
    total_tickets       = db.query(Ticket).count()
    open_tickets        = db.query(Ticket).filter(Ticket.status == "open").count()
    escalated_tickets   = db.query(Ticket).filter(Ticket.status == "escalated").count()
    resolved_tickets    = db.query(Ticket).filter(Ticket.status == "resolved").count()
    total_customers     = db.query(Customer).count()

    # Top intents
    intents = (
        db.query(Conversation.intent, func.count(Conversation.intent).label("count"))
        .group_by(Conversation.intent)
        .order_by(func.count(Conversation.intent).desc())
        .limit(7)
        .all()
    )

    # Messages per channel
    channels = (
        db.query(Conversation.channel, func.count(Conversation.channel).label("count"))
        .group_by(Conversation.channel)
        .all()
    )

    # Last 7 days activity
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    recent = db.query(Conversation).filter(
        Conversation.created_at >= seven_days_ago
    ).count()

    return {
        "total_conversations": total_conversations,
        "total_tickets":       total_tickets,
        "open_tickets":        open_tickets,
        "escalated_tickets":   escalated_tickets,
        "resolved_tickets":    resolved_tickets,
        "total_customers":     total_customers,
        "recent_7_days":       recent,
        "top_intents": [
            {"intent": i, "count": c} for i, c in intents
        ],
        "channels": [
            {"channel": ch, "count": c} for ch, c in channels
        ],
    }


@router.get("/tickets")
def get_tickets(
    status: str = None,
    limit:  int = 50,
    db: Session = Depends(get_db)
):
    """List tickets — optionally filter by status."""
    query = db.query(Ticket).order_by(Ticket.created_at.desc())
    if status:
        query = query.filter(Ticket.status == status)
    tickets = query.limit(limit).all()
    return [
        {
            "id":         t.id,
            "user_id":    t.user_id,
            "channel":    t.channel,
            "intent":     t.intent,
            "message":    t.message,
            "status":     t.status,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
            "resolved_at":t.resolved_at.strftime("%Y-%m-%d %H:%M") if t.resolved_at else None,
        }
        for t in tickets
    ]


@router.patch("/tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Mark a ticket as resolved."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return {"error": "Ticket not found"}
    ticket.status      = "resolved"
    ticket.resolved_at = datetime.datetime.utcnow()
    db.commit()
    return {"status": "resolved", "ticket_id": ticket_id}


@router.get("/conversations")
def get_conversations(limit: int = 50, db: Session = Depends(get_db)):
    """Recent conversations."""
    convos = (
        db.query(Conversation)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id":         c.id,
            "user_id":    c.user_id,
            "channel":    c.channel,
            "message":    c.message,
            "reply":      c.reply,
            "intent":     c.intent,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
        }
        for c in convos
    ]