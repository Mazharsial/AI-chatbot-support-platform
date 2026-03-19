# AI Customer Support Platform
### Built 100% free — no paid APIs required

## Free Tech Stack
| What          | Tool                      | Cost  |
|---------------|---------------------------|-------|
| AI / LLM      | Groq API (LLaMA 3)        | Free  |
| Chat channel  | Telegram Bot API          | Free  |
| Database      | SQLite                    | Free  |
| Backend       | FastAPI + Python          | Free  |
| Embeddings    | sentence-transformers     | Free  |
| Vector search | ChromaDB (local)          | Free  |
| Hosting       | Render.com free tier      | Free  |

## Project Structure
```
ai-support-platform/
├── app/
│   ├── main.py              ← FastAPI app entry point
│   ├── config.py            ← All settings from .env
│   ├── database.py          ← SQLite models + DB session
│   ├── api/
│   │   ├── tickets.py       ← Ticket CRUD endpoints (Phase 5)
│   │   └── analytics.py     ← Dashboard data (Phase 6)
│   ├── ai/
│   │   ├── intent_classifier.py   ← Detect user intent (Phase 3)
│   │   ├── response_generator.py  ← Generate AI reply (Phase 3)
│   │   └── knowledge_base.py      ← FAQ vector search (Phase 3)
│   ├── channels/
│   │   ├── telegram_bot.py  ← Telegram channel (Phase 4)
│   │   └── web_chat.py      ← Website widget (Phase 5)
│   └── services/
│       └── ticket_service.py ← Ticket business logic (Phase 5)
├── tests/
│   └── test_setup.py        ← Run to verify setup
├── scripts/
│   └── seed_faq.py          ← Add sample FAQ data
├── requirements.txt
├── .env.example             ← Copy to .env and add your keys
└── .gitignore
```

## Quick Start
```bash
# 1. Clone and enter project
cd ai-support-platform

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install packages
pip install -r requirements.txt

# 4. Add your keys
cp .env.example .env
# Edit .env and add GROQ_API_KEY and TELEGRAM_TOKEN

# 5. Verify everything works
python tests/test_setup.py

# 6. Start the server
uvicorn app.main:app --reload
```

## Build Phases
- **Phase 1** (current) — Project structure + environment
- **Phase 2** — Database models + seed data
- **Phase 3** — AI engine (intent + response + FAQ)
- **Phase 4** — Telegram bot (first live channel)
- **Phase 5** — FastAPI endpoints + website chat widget
- **Phase 6** — Analytics dashboard + deploy to Render.com
