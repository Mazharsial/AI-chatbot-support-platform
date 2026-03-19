"""
Phase 1 Setup Checker — run this to verify everything is installed correctly.

Usage:
    python tests/test_setup.py

A green ALL CHECKS PASSED means you are ready to start Phase 2.
"""

import os
import sys
import platform

# Make sure the project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

PASS  = "[  OK  ]"
FAIL  = "[ FAIL ]"
WARN  = "[ WARN ]"

errors   = []
warnings = []

def check(label, ok, msg_fail="", msg_warn="", is_warn=False):
    if ok:
        print(f"  {PASS}  {label}")
    elif is_warn:
        print(f"  {WARN}  {label} — {msg_warn}")
        warnings.append(label)
    else:
        print(f"  {FAIL}  {label} — {msg_fail}")
        errors.append(label)


print()
print("=" * 52)
print("   AI Support Platform — Phase 1 Setup Checker")
print("=" * 52)

# ── 1. Python version ─────────────────────────────────────────
print("\n  Python")
py = platform.python_version()
major, minor, _ = py.split(".")
check(
    f"Python {py}",
    int(major) == 3 and int(minor) >= 10,
    msg_fail="Need Python 3.10 or higher. Download from python.org"
)

# ── 2. .env file ──────────────────────────────────────────────
print("\n  Config files")
from pathlib import Path

check(".env file exists",
      Path(".env").exists(),
      msg_fail="Copy .env.example to .env and fill in your keys")

check(".env.example exists",
      Path(".env.example").exists(),
      msg_fail="Missing .env.example — re-download the project")

check("requirements.txt exists",
      Path("requirements.txt").exists(),
      msg_fail="Missing requirements.txt")

# ── 3. Packages ───────────────────────────────────────────────
print("\n  Packages")
packages = [
    ("fastapi",               "fastapi"),
    ("uvicorn",               "uvicorn[standard]"),
    ("groq",                  "groq"),
    ("sqlalchemy",            "sqlalchemy"),
    ("aiosqlite",             "aiosqlite"),
    ("dotenv",                "python-dotenv"),
    ("telegram",              "python-telegram-bot"),
    ("chromadb",              "chromadb"),
    ("sentence_transformers", "sentence-transformers"),
    ("httpx",                 "httpx"),
    ("pydantic_settings",     "pydantic-settings"),
]
for module, pip_name in packages:
    try:
        __import__(module)
        check(pip_name, True)
    except ImportError:
        check(pip_name, False,
              msg_fail=f"Run: pip install {pip_name}")

# ── 4. Load .env values ───────────────────────────────────────
print("\n  API Keys")
from dotenv import load_dotenv
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY", "")
tg_token = os.getenv("TELEGRAM_TOKEN", "")

groq_set = bool(groq_key) and groq_key != "your_groq_api_key_here"
tg_set   = bool(tg_token) and tg_token != "your_telegram_bot_token_here"

check("GROQ_API_KEY set in .env",
      groq_set,
      msg_fail="Get free key at console.groq.com then add to .env")

check("TELEGRAM_TOKEN set in .env",
      tg_set,
      msg_fail="Get free token from @BotFather on Telegram then add to .env",
      is_warn=not tg_set)

# ── 5. Live Groq API call ─────────────────────────────────────
print("\n  Live API Test")
if groq_set:
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user",
                        "content": "Reply with exactly the word: ready"}],
            max_tokens=5,
            temperature=0,
        )
        reply = r.choices[0].message.content.strip()
        check(f"Groq API live (model replied: '{reply}')", True)
    except Exception as e:
        check("Groq API live call", False,
              msg_fail=f"{e}")
else:
    check("Groq API live call", False,
          msg_fail="Set GROQ_API_KEY first")

# ── 6. Database creation ──────────────────────────────────────
print("\n  Database")
try:
    from app.database import init_db, SessionLocal, Ticket, Conversation, Customer, FAQEntry
    init_db()
    db = SessionLocal()
    tables = {
        "customers":     db.query(Customer).count(),
        "conversations": db.query(Conversation).count(),
        "tickets":       db.query(Ticket).count(),
        "faq_entries":   db.query(FAQEntry).count(),
    }
    db.close()
    for table, count in tables.items():
        check(f"Table '{table}' created ({count} rows)", True)
except Exception as e:
    check("SQLite database + tables", False, msg_fail=str(e))

# ── 7. FastAPI app import ─────────────────────────────────────
print("\n  App")
try:
    from app.main import app
    check("app/main.py imports cleanly", True)
except Exception as e:
    check("app/main.py imports cleanly", False, msg_fail=str(e))

# ── Summary ───────────────────────────────────────────────────
print()
print("=" * 52)
if not errors:
    print("  ALL CHECKS PASSED — ready to start Phase 2!")
    if warnings:
        print(f"  {len(warnings)} warning(s) — not blocking, fix when you can.")
else:
    print(f"  {len(errors)} error(s) to fix before continuing:")
    for e in errors:
        print(f"    - {e}")
print("=" * 52)
print()
