import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# =========================
# ALL SUPPORTED INTENTS
# =========================

INTENTS = [
    # Core Support
    "order_status", "refund", "complaint", "booking", "reschedule",
    "cancel_order", "change_order", "delivery_issue", "delay",

    # Product & Info
    "product_info", "pricing", "availability",

    # Technical & Account
    "technical_issue", "account_issue", "payment_issue",

    # Conversation
    "greeting", "goodbye", "thanks",

    # Feedback
    "feedback", "follow_up", "confirmation",

    # AI / fallback
    "faq", "unknown", "human",

    # 🔥 Advanced Sales
    "lead_capture", "lead_qualification", "lead_high_intent",
    "lead_low_intent", "demo_request", "pricing_negotiation",
    "contact_request", "callback_request",
]

# =========================
# FREE MODELS (OpenRouter)
# =========================

FREE_MODELS = [
    "google/gemma-3-4b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "deepseek/deepseek-r1-distill-qwen-7b:free",
    "microsoft/phi-3-mini-128k-instruct:free",
]

# =========================
# PROMPT (ADVANCED)
# =========================

PROMPT = """You are an intent classifier for a customer support chatbot.

Classify the customer message into EXACTLY ONE of these labels:

order_status, refund, complaint, booking, reschedule,
cancel_order, change_order, delivery_issue, delay,
product_info, pricing, availability,
technical_issue, account_issue, payment_issue,
greeting, goodbye, thanks,
feedback, follow_up, confirmation,
faq, human, unknown,
lead_capture, lead_qualification, lead_high_intent,
lead_low_intent, demo_request, pricing_negotiation,
contact_request, callback_request

Rules:
- Reply with ONLY the label — no explanation, no punctuation
- angry or frustrated = complaint
- wants person, agent, human = human
- delivery, tracking = order_status
- refund, return, money back = refund
- cancel order = cancel_order
- modify/change order = change_order
- delay, late = delay
- book, appointment, schedule = booking
- reschedule = reschedule
- greetings like hi, hello = greeting
- thanks = thanks
- bye, goodbye = goodbye
- payment failed = payment_issue
- login, password, account = account_issue
- bug, error, not working = technical_issue
- interested, buy, purchase = lead_high_intent
- exploring, just looking = lead_low_intent
- demo, trial = demo_request
- call me, contact me = callback_request
- general question = faq
- unclear = unknown

Examples:
"where is my order" → order_status
"I want a refund" → refund
"this is terrible service" → complaint
"book appointment tomorrow 3pm" → booking
"hi" → greeting
"I want to buy this" → lead_high_intent
"can you call me" → callback_request

Message: "{message}"
Label:"""

# =========================
# KEYWORD FALLBACK (FAST)
# =========================

STATIC_INTENTS = {
    "refund": ["refund", "money back", "return"],
    "order_status": ["where is my order", "track", "delivery", "shipped", "order status"],
    "human": ["human", "agent", "person", "staff"],
    "complaint": ["terrible", "awful", "worst", "angry", "frustrated", "bad service"],
    "booking": ["book", "appointment", "schedule", "reserve"],
    "reschedule": ["reschedule", "change time"],
    "cancel_order": ["cancel order"],
    "change_order": ["change order", "modify order"],
    "delay": ["late", "delay"],

    "greeting": ["hi", "hello", "hey"],
    "goodbye": ["bye", "goodbye"],
    "thanks": ["thanks", "thank you"],

    "payment_issue": ["payment failed", "transaction failed", "card declined"],
    "account_issue": ["login", "account", "password"],
    "technical_issue": ["error", "bug", "not working", "crash"],

    "product_info": ["product", "details", "features"],
    "pricing": ["price", "cost"],
    "availability": ["available", "in stock"],

    "lead_high_intent": ["buy", "purchase", "interested", "get started"],
    "lead_low_intent": ["just looking", "exploring"],
    "demo_request": ["demo", "trial"],
    "callback_request": ["call me", "contact me", "phone"],
}


def classify_by_keywords(message: str) -> str:
    """Fast keyword-based fallback classifier."""
    msg = message.lower()
    for intent, keywords in STATIC_INTENTS.items():
        for kw in keywords:
            if kw in msg:
                return intent
    return "unknown"


def classify_intent(message: str) -> str:
    """Hybrid intent classifier: LLM + keyword fallback"""

    # 🔹 Step 1: Try OpenRouter models
    for model in FREE_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": PROMPT.format(message=message)
                }],
                max_tokens=10,
                temperature=0,
            )

            label = response.choices[0].message.content.strip().lower()
            label = label.replace(".", "").replace("'", "").strip()

            if label in INTENTS:
                print(f"  Intent via API ({model.split('/')[1]}): {label}")
                return label

        except Exception as e:
            print(f"  Model {model.split('/')[1]} failed: {str(e)[:50]}")
            time.sleep(1)
            continue

    # 🔹 Step 2: Keyword fallback (always works)
    label = classify_by_keywords(message)
    print(f"  Intent via keywords: {label}")
    return label