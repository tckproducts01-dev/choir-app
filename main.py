import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text

# --------------------
# Database Setup
# --------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # For Postgres on Render
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # For local development (SQLite)
    engine = create_engine("sqlite:///songs.db", connect_args={"check_same_thread": False})

conn = engine.connect()

# Create table if not exists
conn.execute(text("""
CREATE TABLE IF NOT EXISTS songs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    lyrics TEXT NOT NULL
)
"""))
conn.commit()

# --------------------
# FastAPI Setup
# --------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --------------------
# Routes
# --------------------

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin/add-song")
def add_song_form(request: Request):
    return templates.TemplateResponse("add_song.html", {"request": request})

@app.post("/admin/add-song")
def add_song(title: str = Form(...), lyrics: str = Form(...)):
    conn.execute(text("INSERT INTO songs (title, lyrics) VALUES (:title, :lyrics)"),
                 {"title": title, "lyrics": lyrics})
    conn.commit()
    return RedirectResponse(url="/admin/songs", status_code=303)

@app.get("/admin/songs")
def list_songs(request: Request):
    result = conn.execute(text("SELECT id, title FROM songs ORDER BY id DESC"))
    songs = result.fetchall()
    return templates.TemplateResponse("songs.html", {"request": request, "songs": songs})

@app.get("/admin/songs/{song_id}")
def view_song(song_id: int, request: Request):
    result = conn.execute(text("SELECT id, title, lyrics FROM songs WHERE id=:id"), {"id": song_id})
    song = result.fetchone()
    if not song:
        return RedirectResponse(url="/admin/songs", status_code=303)
    return templates.TemplateResponse("song_detail.html", {"request": request, "song": song})

@app.get("/admin/songs/{song_id}/edit")
def edit_song_form(song_id: int, request: Request):
    result = conn.execute(text("SELECT id, title, lyrics FROM songs WHERE id=:id"), {"id": song_id})
    song = result.fetchone()
    return templates.TemplateResponse("edit_song.html", {"request": request, "song": song})

@app.post("/admin/songs/{song_id}/edit")
def edit_song(song_id: int, title: str = Form(...), lyrics: str = Form(...)):
    conn.execute(text("UPDATE songs SET title=:title, lyrics=:lyrics WHERE id=:id"),
                 {"title": title, "lyrics": lyrics, "id": song_id})
    conn.commit()
    return RedirectResponse(url=f"/admin/songs/{song_id}", status_code=303)

@app.get("/admin/songs/{song_id}/delete")
def delete_song(song_id: int):
    conn.execute(text("DELETE FROM songs WHERE id=:id"), {"id": song_id})
    conn.commit()
    return RedirectResponse(url="/admin/songs", status_code=303)
