import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS persone (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cognome TEXT,
    nome TEXT,
    luogo_nascita TEXT,
    data_nascita TEXT,
    nome_padre TEXT,
    nome_madre TEXT
)
""")

conn.commit()
conn.close()

print("✅ Database inizializzato.")
