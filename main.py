import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --------------------------------------------------
# Database Setup
# --------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./songs.db"  # fallback for local dev
)

# Ensure compatibility with psycopg on Render
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    lyrics = Column(Text, nullable=False)


# Create tables if they don’t exist
Base.metadata.create_all(bind=engine)

# --------------------------------------------------
# FastAPI App
# --------------------------------------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin/songs")
async def list_songs(request: Request):
    db = next(get_db())
    songs = db.query(Song).all()
    return templates.TemplateResponse("list_songs.html", {"request": request, "songs": songs})


@app.get("/admin/songs/{song_id}")
async def view_song(song_id: int, request: Request):
    db = next(get_db())
    song = db.query(Song).filter(Song.id == song_id).first()
    return templates.TemplateResponse("view_song.html", {"request": request, "song": song})


@app.get("/admin/songs/{song_id}/edit")
async def edit_song(song_id: int, request: Request):
    db = next(get_db())
    song = db.query(Song).filter(Song.id == song_id).first()
    return templates.TemplateResponse("edit_song.html", {"request": request, "song": song})


@app.post("/admin/songs/{song_id}/edit")
async def update_song(song_id: int, title: str = Form(...), lyrics: str = Form(...)):
    db = next(get_db())
    song = db.query(Song).filter(Song.id == song_id).first()
    if song:
        song.title = title
        song.lyrics = lyrics
        db.commit()
    return RedirectResponse(url=f"/admin/songs/{song_id}", status_code=303)


@app.get("/admin/songs/{song_id}/delete")
async def delete_song(song_id: int):
    db = next(get_db())
    song = db.query(Song).filter(Song.id == song_id).first()
    if song:
        db.delete(song)
        db.commit()
    return RedirectResponse(url="/admin/songs", status_code=303)


@app.get("/admin/add-song")
async def add_song_form(request: Request):
    return templates.TemplateResponse("add_song.html", {"request": request})


@app.post("/admin/add-song")
async def add_song(title: str = Form(...), lyrics: str = Form(...)):
    db = next(get_db())
    new_song = Song(title=title, lyrics=lyrics)
    db.add(new_song)
    db.commit()
    return RedirectResponse(url="/admin/songs", status_code=303)
