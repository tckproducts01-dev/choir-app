from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from starlette.status import HTTP_303_SEE_OTHER

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize database
def init_db():
    conn = sqlite3.connect("songs.db")
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

# ------------------------
# Home page
# ------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# ------------------------
# List all songs
# ------------------------
@app.get("/admin/songs", response_class=HTMLResponse)
async def list_songs(request: Request):
    conn = sqlite3.connect("songs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM songs ORDER BY id DESC")
    songs = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("songs.html", {"request": request, "songs": songs})

# ------------------------
# Add new song
# ------------------------
@app.get("/admin/add-song", response_class=HTMLResponse)
async def add_song_form(request: Request):
    return templates.TemplateResponse("add_song.html", {"request": request})

@app.post("/admin/add-song")
async def add_song(title: str = Form(...), lyrics: str = Form(...)):
    conn = sqlite3.connect("songs.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO songs (title, lyrics) VALUES (?, ?)", (title, lyrics))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin/songs", status_code=HTTP_303_SEE_OTHER)

# ------------------------
# View song lyrics
# ------------------------
@app.get("/admin/songs/{song_id}", response_class=HTMLResponse)
async def view_song(request: Request, song_id: int):
    conn = sqlite3.connect("songs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, lyrics FROM songs WHERE id = ?", (song_id,))
    song = cursor.fetchone()
    conn.close()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return templates.TemplateResponse("view_song.html", {"request": request, "song": song})

# ------------------------
# Edit song
# ------------------------
@app.get("/admin/songs/{song_id}/edit", response_class=HTMLResponse)
async def edit_song_form(request: Request, song_id: int):
    conn = sqlite3.connect("songs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, lyrics FROM songs WHERE id = ?", (song_id,))
    song = cursor.fetchone()
    conn.close()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return templates.TemplateResponse("edit_song.html", {"request": request, "song": song})

@app.post("/admin/songs/{song_id}/edit")
async def edit_song(song_id: int, title: str = Form(...), lyrics: str = Form(...)):
    conn = sqlite3.connect("songs.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE songs SET title=?, lyrics=? WHERE id=?", (title, lyrics, song_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/admin/songs/{song_id}", status_code=HTTP_303_SEE_OTHER)

# ------------------------
# Delete song
# ------------------------
@app.get("/admin/songs/{song_id}/delete")
async def delete_song(song_id: int):
    conn = sqlite3.connect("songs.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM songs WHERE id=?", (song_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin/songs", status_code=HTTP_303_SEE_OTHER)
