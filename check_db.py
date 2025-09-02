import sqlite3

# Connect to the database file
conn = sqlite3.connect("songs.db")
cursor = conn.cursor()

print("📂 Checking database...")

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# Show table schema for 'songs'
if ('songs',) in tables:
    cursor.execute("PRAGMA table_info(songs);")
    schema = cursor.fetchall()
    print("\nSongs Table Schema:")
    for column in schema:
        print(column)

conn.close()
