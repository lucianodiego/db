# -*- coding: utf-8 -*-

# Import delle librerie necessarie
import os
import psycopg2 # Libreria per connettersi a PostgreSQL
from psycopg2.extras import DictCursor
import math
from flask import Flask, request, render_template

# --- Configurazione Iniziale ---
app = Flask(__name__)

DEFAULT_RESULTS_PER_PAGE = 50

# --- Funzioni di Connessione e Query per PostgreSQL ---
def get_db_connection():
    """Crea una connessione al database PostgreSQL su Render."""
    conn_url = os.environ.get('DATABASE_URL')
    if not conn_url:
        raise RuntimeError("DATABASE_URL non è impostata. Assicurati di averla aggiunta su Render.")
    
    conn = psycopg2.connect(conn_url)
    return conn

def query_db(query, params=()):
    """Esegue una query di selezione su PostgreSQL e restituisce tutti i risultati."""
    conn = get_db_connection()
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()
    conn.close()
    return results

def count_query_db(query, params=()):
    """Esegue una query di conteggio su PostgreSQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
    conn.close()
    return count

# --- ROTTA DI SETUP ---
@app.route('/setup-database-online-super-segreto-12345')
def setup_online_db():
    """
    Questa rotta crea la tabella e la popola con dati di esempio.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS persone (
                id SERIAL PRIMARY KEY,
                cognome VARCHAR(255),
                nome VARCHAR(255),
                luogo_nascita VARCHAR(255),
                data_nascita VARCHAR(20),
                nome_padre VARCHAR(255),
                nome_madre VARCHAR(255)
            );
            """)
            
            # Controlla se la tabella è vuota prima di inserire
            cur.execute("SELECT COUNT(*) FROM persone;")
            if cur.fetchone()[0] == 0:
                persone_da_inserire = [
                    ('Rossi', 'Mario', 'Roma', '1990', 'Giuseppe', 'Maria'),
                    ('Bianchi', 'Luigi', 'Milano', '1988', 'Antonio', 'Anna'),
                    ('Verdi', 'Giulia', 'Napoli', '1992', 'Francesco', 'Laura'),
                    ('Russo', 'Paolo', 'Torino', '1990', 'Salvatore', 'Angela'),
                ]
                
                # Usa un ciclo per inserire i dati di esempio
                for persona in persone_da_inserire:
                    cur.execute("""
                        INSERT INTO persone (cognome, nome, luogo_nascita, data_nascita, nome_padre, nome_madre) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, persona)
                msg = "Setup completato! Tabella creata e popolata."
            else:
                msg = "Setup non necessario. La tabella contiene già dati."

        conn.commit()
        conn.close()
        return f"<h1>{msg}</h1>"
    except Exception as e:
        return f"<h1>Errore durante il setup!</h1><p>{e}</p>"

# --- ROTTA PRINCIPALE ---
@app.route("/", methods=["GET", "POST"])
def index():
    page = request.args.get('page', 1, type=int)
    risultati = []
    total_pages = 0
    total_results = 0
    is_search_active = False
    
    # Prende i parametri di ricerca dalla richiesta
    search_params = {
        'cognome_testo': request.args.get('cognome_testo', ''),
        'cognome_tipo': request.args.get('cognome_tipo', 'inizia'),
        # Aggiungi qui altri campi se necessario
    }

    if request.method == 'POST':
        page = 1
        search_params['cognome_testo'] = request.form.get('cognome_testo', '')
        search_params['cognome_tipo'] = request.form.get('cognome_tipo', 'inizia')

    where_clauses = []
    query_params = []

    if search_params['cognome_testo']:
        is_search_active = True
        testo = search_params['cognome_testo']
        tipo = search_params['cognome_tipo']
        
        if tipo == "esatto":
            filtro = testo
        elif tipo == "inizia":
            filtro = f"{testo}%"
        else: # contiene
            filtro = f"%{testo}%"
        
        # Usa ILIKE per la ricerca case-insensitive
        where_clauses.append("cognome ILIKE %s")
        query_params.append(filtro)

    if where_clauses:
        sql_where_string = " AND ".join(where_clauses)
        
        count_query = f"SELECT COUNT(*) FROM persone WHERE {sql_where_string}"
        total_results = count_query_db(count_query, tuple(query_params))
        total_pages = math.ceil(total_results / DEFAULT_RESULTS_PER_PAGE)
        
        offset = (page - 1) * DEFAULT_RESULTS_PER_PAGE
        
        data_query = f"SELECT * FROM persone WHERE {sql_where_string} ORDER BY cognome, nome LIMIT %s OFFSET %s"
        final_params = tuple(query_params) + (DEFAULT_RESULTS_PER_PAGE, offset)
        risultati = query_db(data_query, final_params)

    return render_template(
        "index.html",
        risultati=risultati,
        page=page,
        total_pages=total_pages,
        total_results=total_results,
        search_params=search_params,
        is_search_active=is_search_active
    )

if __name__ == "__main__":
    app.run(debug=True)
