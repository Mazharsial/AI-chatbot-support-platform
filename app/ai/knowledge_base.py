# Phase 3 — FAQ knowledge base using ChromaDB + sentence-transformers
# Embeds FAQ pairs locally (free, offline). Semantic search before calling Groq.
"""
Stores FAQ question-answer pairs locally using ChromaDB.
Uses sentence-transformers to embed text — 100% free, runs offline.
Searched BEFORE calling Groq to save API calls.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import chromadb
from sentence_transformers import SentenceTransformer
from app.database import SessionLocal, FAQEntry

# Local ChromaDB — stores data in a folder called chroma_db/
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection     = chroma_client.get_or_create_collection(name="faqs")

# Free embedding model — downloads once (~90MB), runs offline forever
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def load_faqs_into_chromadb():
    """
    Reads all FAQ rows from SQLite and embeds them into ChromaDB.
    Call this once after seeding the database.
    """
    db    = SessionLocal()
    faqs  = db.query(FAQEntry).filter(FAQEntry.active == True).all()
    db.close()

    if not faqs:
        print("No FAQ entries found. Run: python scripts/seed_faq.py first.")
        return

    # Clear existing entries so we don't get duplicates on re-load
    existing = collection.count()
    if existing > 0:
        collection.delete(where={"source": "faq"})

    questions  = [f.question for f in faqs]
    answers    = [f.answer   for f in faqs]
    ids        = [f.id       for f in faqs]

    embeddings = embedder.encode(questions).tolist()

    collection.add(
        ids        = ids,
        embeddings = embeddings,
        documents  = questions,
        metadatas  = [{"answer": a, "source": "faq"} for a in answers],
    )
    print(f"Loaded {len(faqs)} FAQs into ChromaDB.")


def search_faq(query: str, threshold: float = 0.40) -> str:
    """
    Searches FAQ for the closest match to the query.
    Returns the answer string if confident, empty string if no good match.
    """
    if collection.count() == 0:
        return ""

    try:
        query_embedding = embedder.encode([query]).tolist()
        results = collection.query(
            query_embeddings = query_embedding,
            n_results        = 1,
        )

        distances = results["distances"][0]
        metadatas = results["metadatas"][0]

        if not distances:
            return ""

        # ChromaDB distance: lower = more similar. Convert to similarity score.
        similarity = 1 - distances[0]

        if similarity >= threshold:
            return metadatas[0]["answer"]

        return ""

    except Exception as e:
        print(f"FAQ search error: {e}")
        return ""