import os
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError, ArgumentError
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# -----------------------
# Environment + DB Config
# -----------------------
DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
SessionLocal = None
db_error = None

try:
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except (ArgumentError, ValueError) as e:
    db_error = f"❌ Database configuration error: {e}"
except Exception as e:
    db_error = f"❌ Unexpected error while setting up DB: {e}"

Base = declarative_base()

# -----------------------
# Models
# -----------------------
class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    lyrics = Column(Text, nullable=False)

# Create tables only if DB works
if engine and not db_error:
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as e:
        db_error = f"❌ Failed to create tables: {e}"

# -----------------------
# FastAPI setup
# -----------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# -----------------------
# Dependency
# -----------------------
def get_db():
    if not SessionLocal:
        raise RuntimeError("Database is not available")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------
# Routes
# -----------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    songs = db.query(Song).all() if not db_error else []
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "songs": songs, "db_error": db_error},
    )

@app.post("/add", response_class=HTMLResponse)
def add_song(
    request: Request,
    title: str = Form(...),
    lyrics: str = Form(...),
    db: Session = Depends(get_db),
):
    if db_error:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "songs": [], "db_error": db_error},
        )
    new_song = Song(title=title, lyrics=lyrics)
    db.add(new_song)
    db.commit()
    songs = db.query(Song).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "songs": songs, "db_error": None},
    )

@app.get("/health")
def health():
    if db_error:
        return {"status": "error", "message": db_error}
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "message": "Database connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
