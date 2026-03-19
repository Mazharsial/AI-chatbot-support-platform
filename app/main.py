from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.database import init_db
from app.config import settings
from app.api.chat      import router as chat_router
from app.api.analytics import router as analytics_router

app = FastAPI(
    title=settings.app_name,
    description="AI-powered customer support — built 100% free",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router,      prefix="/chat",      tags=["Chat"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])


@app.on_event("startup")
def on_startup():
    init_db()
    print(f"\n{settings.app_name} is running!")
    print("Docs:        http://localhost:8000/docs")
    print("Dashboard:   http://localhost:8000/dashboard")
    print("Widget:      http://localhost:8000/widget\n")


@app.get("/")
def root():
    return {"message": f"{settings.app_name} is running", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/widget", response_class=HTMLResponse)
def widget():
    path = Path("chat_widget.html")
    if path.exists():
        return HTMLResponse(content=path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h2>chat_widget.html not found</h2>")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    path = Path("dashboard.html")
    if path.exists():
        return HTMLResponse(content=path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h2>dashboard.html not found</h2>")