import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from app.ai.knowledge_base import search_faq

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

FREE_MODELS = [
    "google/gemma-3-4b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "deepseek/deepseek-r1-distill-qwen-7b:free",
    "microsoft/phi-3-mini-128k-instruct:free",
]

SYSTEM_PROMPT = """You are a friendly and professional customer support assistant.
- Keep replies to 2-3 sentences max
- Be empathetic and professional
- Never make up order details or prices
- If you cannot help, offer to escalate to a human agent"""

INTENT_CONTEXT = {
    # Core Support
    "order_status": "Customer is asking about their order status. Ask for their order ID politely if not provided.",
    "refund": "Customer wants a refund. Be empathetic. Ask for order ID and reason if not provided.",
    "complaint": "Customer is unhappy. Apologize sincerely first, then ask how you can help.",
    "booking": "Customer wants to book an appointment. Confirm their preferred date and time.",
    "human": "Customer wants a human agent. Acknowledge this warmly and confirm escalation.",
    "faq": "Answer the general question helpfully and concisely.",
    "unknown": "Politely ask the customer to clarify what they need help with.",

    # Conversation Flow
    "greeting": "Customer is greeting. Respond warmly and offer help.",
    "goodbye": "Customer is ending conversation. Respond politely.",
    "thanks": "Customer is thanking. Respond courteously and offer further help.",

    # Orders & Delivery
    "cancel_order": "Customer wants to cancel order. Ask for order ID.",
    "change_order": "Customer wants to modify order. Ask for order ID and changes.",
    "delivery_issue": "Customer reports delivery problem. Apologize and ask for order ID.",
    "delay": "Customer is concerned about delay. Apologize and reassure.",

    # Payments & Account
    "payment_issue": "Customer has payment issues. Ask for details and reassure support.",
    "account_issue": "Customer has login/account problem. Assist or escalate securely.",

    # Product & Business Info
    "product_info": "Customer wants product details. Provide concise and helpful info.",
    "pricing": "Customer is asking about pricing. Provide general info carefully.",
    "availability": "Customer is asking about product/service availability.",

    # Technical Support
    "technical_issue": "Customer is facing technical issue. Ask for details and device info.",

    # Feedback & Follow-up
    "feedback": "Customer is giving feedback. Appreciate and acknowledge.",
    "follow_up": "Customer is following up on previous issue. Check and update status.",
    "confirmation": "Customer wants confirmation. Confirm clearly and politely.",

    # Booking Advanced
    "reschedule": "Customer wants to reschedule booking. Ask for new date/time.",

    # 🔥 Sales & Lead System (Advanced)
    "lead_capture": "Customer is interested. Capture contact details naturally.",
    "lead_qualification": "Customer is a potential lead. Ask about needs, budget, timeline.",
    "lead_high_intent": "Customer shows strong buying intent. Prioritize conversion.",
    "lead_low_intent": "Customer is unsure. Educate and build interest.",
    "demo_request": "Customer wants a demo. Schedule and collect details.",
    "pricing_negotiation": "Customer is price-sensitive. Emphasize value.",
    "contact_request": "Customer asks for contact details. Provide or offer callback.",
    "callback_request": "Customer wants a callback. Collect phone/time.",
}

STATIC_RESPONSES = {
    # Core Support
    "order_status": "I'd be happy to check your order status! Could you please share your order ID so I can look into this for you?",
    
    "refund": "I'm sorry to hear you'd like a refund. Could you please provide your order ID and the reason? I'll process this right away.",
    
    "complaint": "I'm really sorry you're experiencing this issue. I understand your frustration. Please describe the problem so I can escalate it immediately.",
    
    "booking": "I'd be happy to confirm your booking! Please share your preferred date and time.",
    
    "human": "I completely understand. I've created a support ticket and a human agent will contact you shortly.",
    
    "faq": "That's a great question! Could you provide a bit more detail so I can give you the most accurate answer?",
    
    "unknown": "I'm here to help! Could you please clarify what you need assistance with today?",

    # Conversation Flow
    "greeting": "Hello! 😊 How can I assist you today?",
    
    "goodbye": "Thank you for reaching out! Have a great day ahead. 👋",
    
    "thanks": "You're most welcome! 😊 Let me know if you need anything else.",

    # Orders & Delivery
    "cancel_order": "I understand you'd like to cancel your order. Please share your order ID so I can process this for you.",
    
    "change_order": "Sure! I can help update your order. Please provide your order ID and the changes you'd like.",
    
    "delivery_issue": "I'm really sorry for the inconvenience with your delivery. Please share your order ID so I can check this for you.",
    
    "delay": "I sincerely apologize for the delay. I'm checking this on priority and will update you shortly.",

    # Payments & Account
    "payment_issue": "I'm sorry you're facing a payment issue. Could you share more details or your transaction ID?",
    
    "account_issue": "I understand you're facing an account issue. Please share basic details so I can assist or escalate this securely.",

    # Product & Business Info
    "product_info": "I'd be happy to help! Please tell me which product you're interested in.",
    
    "pricing": "I'd be happy to help with pricing! Could you specify the product or service you're referring to?",
    
    "availability": "Let me check that for you. Please tell me which product or service you're asking about.",

    # Technical Support
    "technical_issue": "I'm sorry you're experiencing this issue. Could you describe the problem and your device details?",

    # Feedback & Follow-up
    "feedback": "Thank you for your valuable feedback! We truly appreciate it.",
    
    "follow_up": "Thanks for following up. Let me check the latest update for you right away.",
    
    "confirmation": "Your request has been successfully noted and confirmed.",

    # Booking Advanced
    "reschedule": "Sure! I can help reschedule that. Please share your preferred new date and time.",

    # 🔥 Sales & Lead System
    "lead_capture": "That sounds great! 😊 Could you share your email or phone number so our team can assist you further?",
    
    "lead_qualification": "I'd love to understand your needs better. What are you looking to achieve and your preferred timeline?",
    
    "lead_high_intent": "Awesome! 🚀 I can connect you with a specialist right away. Please share your contact details.",
    
    "lead_low_intent": "No worries! 😊 I can share more details to help you decide. What would you like to know?",
    
    "demo_request": "Great choice! 🎯 Please share your preferred date, time, and contact details to schedule a demo.",
    
    "pricing_negotiation": "I understand budget matters. Our solution focuses on long-term value. Would you like a quick breakdown?",
    
    "contact_request": "You can reach our team via email or phone, or I can arrange a callback. What works best for you?",
    
    "callback_request": "Sure! 📞 Please share your phone number and a convenient time, and our team will call you back.",
}


def generate_reply(
    message: str,
    intent: str,
    history: list,
    order_info: str = "",
) -> str:
    # Step 1 — FAQ search (offline, always works)
    if intent in ("faq", "unknown"):
        faq_answer = search_faq(message)
        if faq_answer:
            print("  Reply from FAQ (offline)")
            return faq_answer

    # Step 2 — build messages
    system = SYSTEM_PROMPT
    hint = INTENT_CONTEXT.get(intent, "")
    if hint:
        system += f"\n\nSituation: {hint}"
    if order_info:
        system += f"\n\nOrder info: {order_info}"

    messages = [{"role": "system", "content": system}]
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": message})

    # Step 3 — try OpenRouter models
    # Step 3 — try OpenRouter models with smart retry
      # Step 3 — try OpenRouter models with smart retry
    import random
    random.shuffle(FREE_MODELS)  # randomize so same model isn't hit twice in a row
    for i, model in enumerate(FREE_MODELS):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=150,
                temperature=0.7,
            )
            reply = response.choices[0].message.content.strip()
            if reply:
                print(f"  Reply via {model.split('/')[1]}")
                return reply
        except Exception as e:
            err = str(e)[:60]
            print(f"  Model {model.split('/')[1]} failed: {err}")
            wait = 2 * (i + 1)  # wait 2s, 4s, 6s between retries
            print(f"  Waiting {wait}s before next model...")
            time.sleep(wait)
            continue

    # Step 4 — smart static response (always works, never says "technical issue")
    print("  Reply via static response")
    return STATIC_RESPONSES.get(intent, "I'm here to help! Could you clarify your question?")