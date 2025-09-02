from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

# --- Database (SQLAlchemy) ---
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

BASE_DIR = Path(__file__).resolve().parent
DB_URL = f"sqlite:///{(BASE_DIR / 'songs.db').as_posix()}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    lyrics = Column(Text, nullable=False)

Base.metadata.create_all(bind=engine)

# --- App & Templates ---
app = FastAPI(title="Choir App")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Public root still returns JSON (unchanged) ---
@app.get("/")
def root():
    return {"message": "Choir App is running!"}

# --- Admin: list songs ---
@app.get("/admin", response_class=HTMLResponse)
def admin_list(request: Request):
    with SessionLocal() as db:
        songs = db.query(Song).order_by(Song.title.asc()).all()
    return templates.TemplateResponse("admin_list.html", {"request": request, "songs": songs})

# --- Admin: add song (form) ---
@app.get("/admin/add", response_class=HTMLResponse)
def add_song_form(request: Request):
    return templates.TemplateResponse("admin_add.html", {"request": request})

# --- Admin: add song (submit) ---
@app.post("/admin/add")
def add_song(title: str = Form(...), lyrics: str = Form(...)):
    with SessionLocal() as db:
        db.add(Song(title=title.strip(), lyrics=lyrics.strip()))
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

# --- Admin: delete (we'll add edit in next step) ---
@app.post("/admin/delete/{song_id}")
def delete_song(song_id: int):
    with SessionLocal() as db:
        obj = db.get(Song, song_id)
        if obj:
            db.delete(obj)
            db.commit()
    return RedirectResponse(url="/admin", status_code=303)
