import csv
import sqlite3

# Connessione al database (lo crea se non esiste)
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# --- INIZIO MODIFICHE ---

# 1. Crea la tabella 'persone' se non esiste già.
#    Questo risolve l'errore "no such table".
cursor.execute('''
CREATE TABLE IF NOT EXISTS persone (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cognome TEXT NOT NULL,
    nome TEXT NOT NULL,
    luogo_nascita TEXT,
    data_nascita TEXT,
    nome_padre TEXT,
    nome_madre TEXT
)
''')

# --- FINE MODIFICHE ---


# Il resto del tuo codice rimane invariato
print("Inizio importazione dal file dati.csv...")
try:
    with open("dati.csv", newline='', encoding='latin1') as csvfile:
        # Usiamo DictReader per leggere il CSV basandoci sui nomi delle colonne
        reader = csv.DictReader(csvfile, delimiter=';')
        count = 0
        for row in reader:
            # Controlla che tutte le colonne necessarie esistano nella riga
            if all(k in row for k in ['cognome', 'nome', 'luogo_nascita', 'data_nascita', 'nome_padre', 'nome_madre']):
                cursor.execute("""
                    INSERT INTO persone (cognome, nome, luogo_nascita, data_nascita, nome_padre, nome_madre)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row['cognome'].strip(),
                    row['nome'].strip(),
                    row['luogo_nascita'].strip(),
                    row['data_nascita'].strip(),
                    row['nome_padre'].strip(),
                    row['nome_madre'].strip()
                ))
                count += 1
                # Stampa un aggiornamento ogni 1000 righe
                if count % 1000 == 0:
                    print(f"{count} righe importate...")

    # Salva tutte le modifiche (commit) solo se l'importazione va a buon fine
    conn.commit()
    print(f"✅ Importazione completata! Totale righe importate: {count}")

except FileNotFoundError:
    print("❌ ERRORE: File 'dati.csv' non trovato. Assicurati che sia nella stessa cartella dello script.")
except Exception as e:
    print(f"❌ Si è verificato un errore: {e}")
    # Annulla qualsiasi modifica parziale in caso di errore
    conn.rollback()

finally:
    # Chiudi sempre la connessione al database
    conn.close()

