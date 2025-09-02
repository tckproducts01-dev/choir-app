import sqlite3

# Connect to the database
conn = sqlite3.connect("songs.db")
cursor = conn.cursor()

print("📂 Songs currently in database:")

cursor.execute("SELECT id, title FROM songs")
songs = cursor.fetchall()

if songs:
    for song in songs:
        print(f"ID: {song[0]}, Title: {song[1]}")
else:
    print("No songs found yet.")

conn.close()
