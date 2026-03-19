"""
Seed the database with sample FAQ entries.
Run after Phase 1 setup: python scripts/seed_faq.py

These will be embedded into ChromaDB in Phase 3 for semantic search.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import init_db, SessionLocal, FAQEntry

SAMPLE_FAQS = [
    # General
    {
        "question": "What are your business hours?",
        "answer": "We are available Monday to Saturday, 9 AM to 6 PM PKT.",
        "category": "general",
    },
    {
        "question": "How can I contact human support?",
        "answer": "Type 'human agent' or 'talk to agent' and I will connect you with a real person immediately.",
        "category": "general",
    },
    {
        "question": "Is my payment information safe?",
        "answer": "Yes, all payments go through secure encrypted gateways. We never store card details.",
        "category": "general",
    },
    {
        "question": "What payment methods do you accept?",
        "answer": "We accept JazzCash, EasyPaisa, bank transfer, and cash on delivery.",
        "category": "general",
    },

    # Orders
    {
        "question": "How do I track my order?",
        "answer": "Share your order ID and I will check the status for you right away.",
        "category": "orders",
    },
    {
        "question": "How long does delivery take?",
        "answer": "Standard delivery takes 3 to 5 business days. Express delivery takes 1 to 2 business days.",
        "category": "orders",
    },
    {
        "question": "Do you offer free shipping?",
        "answer": "Yes, free shipping on all orders above Rs. 1000.",
        "category": "orders",
    },
    {
        "question": "Can I change or cancel my order?",
        "answer": "You can cancel or modify your order within 2 hours of placing it. After that, it may have already shipped.",
        "category": "orders",
    },
    {
        "question": "My order has not arrived yet. What should I do?",
        "answer": "Please share your order ID and I will check the latest tracking status for you.",
        "category": "orders",
    },

    # Refunds
    {
        "question": "What is your return policy?",
        "answer": "We accept returns within 30 days of purchase. Items must be unused and in original packaging.",
        "category": "refunds",
    },
    {
        "question": "How do I request a refund?",
        "answer": "Share your order ID and reason for the refund. Refunds are processed within 5 to 7 business days.",
        "category": "refunds",
    },
    {
        "question": "When will I receive my refund?",
        "answer": "Refunds are credited within 5 to 7 business days after approval. JazzCash and EasyPaisa refunds are usually faster.",
        "category": "refunds",
    },

    # Products
    {
        "question": "Are your products original or genuine?",
        "answer": "Yes, all our products are 100% genuine with official warranty where applicable.",
        "category": "products",
    },
    {
        "question": "Do you offer a warranty?",
        "answer": "Yes, most electronics come with a 1-year manufacturer warranty. Check the product page for details.",
        "category": "products",
    },
    {
        "question": "Is the item I want available in stock?",
        "answer": "Please tell me the product name and I will check current availability for you.",
        "category": "products",
    },
]


if __name__ == "__main__":
    init_db()
    db = SessionLocal()

    added = 0
    skipped = 0
    for faq in SAMPLE_FAQS:
        existing = db.query(FAQEntry).filter(
            FAQEntry.question == faq["question"]
        ).first()
        if not existing:
            db.add(FAQEntry(**faq))
            added += 1
        else:
            skipped += 1

    db.commit()
    db.close()

    print(f"FAQ seed complete: {added} added, {skipped} already existed.")
    print("Run 'python scripts/seed_faq.py' again anytime — it won't add duplicates.")
