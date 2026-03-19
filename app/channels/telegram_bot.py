"""
Telegram bot — the first live channel.
Run with: python app/channels/telegram_bot.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    filters, ContextTypes
)
from app.ai.intent_classifier  import classify_intent
from app.ai.response_generator import generate_reply
from app.ai.knowledge_base     import load_faqs_into_chromadb
from app.database import SessionLocal, Conversation, Ticket, Customer
import datetime

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

histories: dict = {}
INTENTS_NEEDING_TICKET = {"complaint", "refund", "human"}


def get_or_create_customer(db, telegram_id: str, name: str) -> Customer:
    customer = db.query(Customer).filter(
        Customer.telegram_id == telegram_id
    ).first()
    if not customer:
        customer = Customer(
            telegram_id    = telegram_id,
            name           = name,
            channel        = "telegram",
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


def save_conversation(db, user_id, channel, message, reply, intent, customer_id):
    db.add(Conversation(
        customer_id = customer_id,
        user_id     = user_id,
        channel     = channel,
        message     = message,
        reply       = reply,
        intent      = intent,
    ))
    db.commit()


def create_ticket_if_needed(db, user_id, channel, intent, message):
    if intent in INTENTS_NEEDING_TICKET:
        status = "escalated" if intent == "human" else "open"
        db.add(Ticket(
            user_id = user_id,
            channel = channel,
            intent  = intent,
            message = message,
            status  = status,
        ))
        db.commit()
        return True
    return False


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "there"
    await update.message.reply_text(
        f"Hello {name}! I'm your AI support assistant.\n\n"
        "I can help you with:\n"
        "- Order status and tracking\n"
        "- Refunds and returns\n"
        "- General questions\n"
        "- Booking and scheduling\n\n"
        "Just type your question and I'll help you right away!"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Here's what I can do:\n\n"
        "/start  — Welcome message\n"
        "/help   — Show this menu\n"
        "/clear  — Clear conversation history\n\n"
        "Or just type any message and I'll respond!\n"
        "Type 'human agent' if you want a real person."
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    histories[user_id] = []
    await update.message.reply_text(
        "Conversation cleared! How can I help you today?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    user_id = str(user.id)
    name    = user.first_name or "Customer"
    text    = update.message.text.strip()

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    if user_id not in histories:
        histories[user_id] = []

    intent = classify_intent(text)

    reply = generate_reply(
        message = text,
        intent  = intent,
        history = histories[user_id],
    )

    if intent == "human":
        reply += (
            "\n\nI've created an urgent support ticket for you. "
            "A human agent will contact you shortly."
        )

    histories[user_id].append({"role": "user",      "content": text})
    histories[user_id].append({"role": "assistant", "content": reply})

    if len(histories[user_id]) > 20:
        histories[user_id] = histories[user_id][-20:]

    db = SessionLocal()
    try:
        customer = get_or_create_customer(db, user_id, name)
        save_conversation(db, user_id, "telegram",
                          text, reply, intent, customer.id)
        ticket_created = create_ticket_if_needed(
            db, user_id, "telegram", intent, text
        )
        if ticket_created:
            print(f"  >> Ticket created — user: {name}, intent: {intent}")
    finally:
        db.close()

    await update.message.reply_text(reply)
    print(f"  [{intent.upper()}] {name}: {text[:50]} → replied")


def run_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("ERROR: TELEGRAM_TOKEN not set in .env")
        return

    print("\n" + "=" * 45)
    print("  AI Support Bot — Telegram Channel")
    print("=" * 45)
    print("  Loading FAQs into ChromaDB...")
    load_faqs_into_chromadb()
    print("  Bot is starting...")
    print("  Open Telegram and message your bot!")
    print("  Press Ctrl+C to stop.")
    print("=" * 45 + "\n")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()