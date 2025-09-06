from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# Load DATABASE_URL from environment (Render → Environment)
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define Song model
class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    lyrics = Column(Text, nullable=False)

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# FastAPI setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Home - list songs
@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    songs = db.query(Song).all()
    return templates.TemplateResponse("index.html", {"request": request, "songs": songs})

# Add new song
@app.post("/add")
def add_song(
    request: Request,
    title: str = Form(...),
    lyrics: str = Form(...),
    db: Session = Depends(get_db)
):
    new_song = Song(title=title, lyrics=lyrics)
    db.add(new_song)
    db.commit()
    db.refresh(new_song)
    return RedirectResponse("/", status_code=303)

# View a single song
@app.get("/song/{song_id}")
def view_song(song_id: int, request: Request, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("song.html", {"request": request, "song": song})
