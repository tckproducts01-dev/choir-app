from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import os

app = FastAPI()

# ========================
# Database Setup
# ========================
DATABASE_URL = os.getenv("DATABASE_URL")

# Fix Render's postgres:// → postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    lyrics = Column(Text, nullable=False)


# Create tables on startup
Base.metadata.create_all(bind=engine)

# ========================
# Templates & Static
# ========================
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ========================
# Routes
# ========================
@app.get("/")
def home(request: Request):
    db = SessionLocal()
    songs = db.query(Song).all()
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "songs": songs})


@app.get("/songs/new")
def new_song_form(request: Request):
    return templates.TemplateResponse("add_song.html", {"request": request})


@app.post("/songs")
def add_song(title: str = Form(...), lyrics: str = Form(...)):
    db = SessionLocal()
    new_song = Song(title=title, lyrics=lyrics)
    db.add(new_song)
    db.commit()
    db.refresh(new_song)
    db.close()
    return RedirectResponse(url="/", status_code=303)


@app.get("/songs/{song_id}")
def view_song(song_id: int, request: Request):
    db = SessionLocal()
    song = db.query(Song).filter(Song.id == song_id).first()
    db.close()
    return templates.TemplateResponse("song_detail.html", {"request": request, "song": song})


# ========================
# Health Check Route
# ========================
@app.get("/health")
def health_check():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)
