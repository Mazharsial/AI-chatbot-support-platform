"""
WebSocket endpoint — powers the website chat widget.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ai.intent_classifier  import classify_intent
from app.ai.response_generator import generate_reply
from app.database import SessionLocal, Conversation, Ticket, Customer
import datetime

router = APIRouter()

# In-memory history per session
histories: dict = {}
INTENTS_NEEDING_TICKET = {"complaint", "refund", "human"}


def get_or_create_web_customer(db, session_id: str) -> Customer:
    customer = db.query(Customer).filter(
        Customer.telegram_id == session_id
    ).first()
    if not customer:
        customer = Customer(
            telegram_id    = session_id,
            name           = "Web Visitor",
            channel        = "web",
            total_messages = "1",
            first_seen     = datetime.datetime.utcnow(),
            last_seen      = datetime.datetime.utcnow(),
        )
        db.add(customer)
    else:
        customer.last_seen      = datetime.datetime.utcnow()
        customer.total_messages = str(int(customer.total_messages or 0) + 1)
    db.commit()
    db.refresh(customer)
    return customer


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    print(f"  Web chat connected: {session_id[:8]}...")

    if session_id not in histories:
        histories[session_id] = []

    # Send welcome message immediately
    await websocket.send_json({
        "type":    "message",
        "sender":  "bot",
        "message": "Hello! I'm your AI support assistant. How can I help you today?"
    })

    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("message", "").strip()
            if not text:
                continue

            # Show typing indicator
            await websocket.send_json({"type": "typing"})

            # AI pipeline
            intent = classify_intent(text)
            reply  = generate_reply(
                message = text,
                intent  = intent,
                history = histories[session_id],
            )

            if intent == "human":
                reply += "\n\nI've created an urgent support ticket. A human agent will contact you shortly."

            # Update history
            histories[session_id].append({"role": "user",      "content": text})
            histories[session_id].append({"role": "assistant", "content": reply})
            if len(histories[session_id]) > 20:
                histories[session_id] = histories[session_id][-20:]

            # Save to database
            db = SessionLocal()
            try:
                customer = get_or_create_web_customer(db, session_id)
                db.add(Conversation(
                    customer_id = customer.id,
                    user_id     = session_id,
                    channel     = "web",
                    message     = text,
                    reply       = reply,
                    intent      = intent,
                ))
                if intent in INTENTS_NEEDING_TICKET:
                    status = "escalated" if intent == "human" else "open"
                    db.add(Ticket(
                        user_id = session_id,
                        channel = "web",
                        intent  = intent,
                        message = text,
                        status  = status,
                    ))
                db.commit()
            finally:
                db.close()

            # Send reply
            await websocket.send_json({
                "type":    "message",
                "sender":  "bot",
                "message": reply,
                "intent":  intent,
            })
            print(f"  [WEB/{intent.upper()}] {text[:40]} → replied")

    except WebSocketDisconnect:
        print(f"  Web chat disconnected: {session_id[:8]}...")
        if session_id in histories:
            del histories[session_id]