from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DB_FILE = "songs.db"

# ? Create database if not exists
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            lyrics TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ========================
# ROUTES
# ========================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin/add-song", response_class=HTMLResponse)
def add_song_form(request: Request):
    return templates.TemplateResponse("add_song.html", {"request": request})

@app.post("/admin/add-song")
def add_song(title: str = Form(...), lyrics: str = Form(...)):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO songs (title, lyrics) VALUES (?, ?)", (title, lyrics))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin/songs", status_code=303)

@app.get("/admin/songs", response_class=HTMLResponse)
def list_songs(request: Request):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM songs")
    songs = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("list_songs.html", {"request": request, "songs": songs})

@app.get("/admin/songs/{song_id}", response_class=HTMLResponse)
def view_song(request: Request, song_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, lyrics FROM songs WHERE id = ?", (song_id,))
    song = cursor.fetchone()

    conn.close()

    if song:
        return templates.TemplateResponse("view_song.html", {"request": request, "song": song})
    else:
        return HTMLResponse(content="<h1>Song not found</h1>", status_code=404)

# ========================
# NEW: EDIT SONG
# ========================

@app.get("/admin/songs/{song_id}/edit", response_class=HTMLResponse)
def edit_song_form(request: Request, song_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, lyrics FROM songs WHERE id = ?", (song_id,))
    song = cursor.fetchone()
    conn.close()

    if song:
        return templates.TemplateResponse("edit_song.html", {"request": request, "song": song})
    else:
        return HTMLResponse(content="<h1>Song not found</h1>", status_code=404)

@app.post("/admin/songs/{song_id}/edit")
def edit_song(song_id: int, title: str = Form(...), lyrics: str = Form(...)):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE songs SET title = ?, lyrics = ? WHERE id = ?", (title, lyrics, song_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/admin/songs/{song_id}", status_code=303)

# ========================
# NEW: DELETE SONG
# ========================

@app.post("/admin/songs/{song_id}/delete")
def delete_song(song_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM songs WHERE id = ?", (song_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin/songs", status_code=303)
