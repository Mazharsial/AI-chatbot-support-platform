"""
Tests the complete AI pipeline end to end.
Run: python tests/test_ai.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai.intent_classifier  import classify_intent
from app.ai.knowledge_base     import load_faqs_into_chromadb, search_faq
from app.ai.response_generator import generate_reply

TEST_MESSAGES = [
    ("Where is my order #1234?",            "order_status"),
    ("I want a refund for my last order",   "refund"),
    ("This product is terrible!",           "complaint"),
    ("What are your business hours?",       "faq"),
    ("I want to talk to a real person",     "human"),
    ("Do you offer free shipping?",         "faq"),
    ("My package has not arrived",          "order_status"),
    ("What payment methods do you accept?", "faq"),
]

print("\n" + "=" * 55)
print("   AI Engine Test")
print("=" * 55)

# Load FAQs into ChromaDB first
print("\nLoading FAQs into ChromaDB...")
load_faqs_into_chromadb()

print("\n--- Intent Classification ---")
passed = 0
for message, expected in TEST_MESSAGES:
    result = classify_intent(message)
    ok     = result == expected
    status = "[  OK  ]" if ok else "[ FAIL ]"
    if ok:
        passed += 1
    print(f"  {status}  '{message[:40]}...' → {result}  (expected: {expected})")

print(f"\n  Score: {passed}/{len(TEST_MESSAGES)} correct")

print("\n--- FAQ Search ---")
faq_tests = [
    "What time do you open?",
    "How long will shipping take?",
    "Can I return my item?",
]
for q in faq_tests:
    answer = search_faq(q)
    found  = bool(answer)
    status = "[  OK  ]" if found else "[ MISS ]"
    preview = answer[:60] + "..." if len(answer) > 60 else answer
    print(f"  {status}  '{q}'")
    if found:
        print(f"           → {preview}")

print("\n--- Full Reply Generation ---")
test_convos = [
    ("I want a refund",          "refund",       []),
    ("Where is my order?",       "order_status", []),
    ("Your service is terrible", "complaint",    []),
]
for msg, intent, history in test_convos:
    reply = generate_reply(msg, intent, history)
    print(f"\n  User   : {msg}")
    print(f"  Intent : {intent}")
    print(f"  Bot    : {reply}")

print("\n" + "=" * 55)
print("  AI Engine test complete!")
print("=" * 55 + "\n")