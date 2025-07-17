# -*- coding: utf-8 -*-

# Import delle librerie necessarie
import os
import psycopg2 # Libreria per connettersi a PostgreSQL
from psycopg2.extras import DictCursor # Per ottenere risultati simili a dizionari
import math
from flask import Flask, request, render_template, flash, redirect, url_for
from datetime import datetime
import csv
import io

# --- Configurazione Iniziale ---
app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.do') 
# Aggiungi una chiave segreta per i messaggi flash. È importante per la sicurezza.
# Su Render, imposta questa come variabile d'ambiente.
app.secret_key = os.environ.get('SECRET_KEY', 'un-segreto-molto-segreto-per-sviluppo-locale')


DEFAULT_RESULTS_PER_PAGE = 20
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# --- Funzioni di Connessione e Query per PostgreSQL (invariate) ---
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

def get_total_record_count():
    """Restituisce il numero totale di record nella tabella persone."""
    try:
        count = count_query_db("SELECT COUNT(*) FROM persone")
    except psycopg2.Error:
        count = 0
    return count

# --- ROTTA DI SETUP (invariata) ---
@app.route('/setup-database-online-super-segreto-12345')
def setup_online_db():
    """
    Questa rotta crea la tabella e la popola con dati di esempio.
    Può essere eseguita più volte: aggiungerà solo i dati non ancora presenti.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS persone (
                id SERIAL PRIMARY KEY,
                cognome VARCHAR(100),
                nome VARCHAR(100),
                luogo_nascita VARCHAR(100),
                data_nascita VARCHAR(20),
                nome_padre VARCHAR(100),
                nome_madre VARCHAR(100)
            );
            """)
            
            persone_da_inserire = [
                ('Rossi', 'Mario', 'Roma', '1990', 'Giuseppe', 'Maria'),
                ('Bianchi', 'Luigi', 'Milano', '1988', 'Antonio', 'Anna'),
                ('Verdi', 'Giulia', 'Napoli', '1992', 'Francesco', 'Laura'),
                ('Russo', 'Paolo', 'Torino', '1990', 'Salvatore', 'Angela'),
                ('Ferrari', 'Chiara', 'Bologna', '1995', 'Roberto', 'Paola'),
                ('Esposito', 'Antonio', 'Napoli', '1985', 'Gennaro', 'Carmela'),
                ('Romano', 'Francesca', 'Roma', '1991', 'Marco', 'Sofia'),
                ('Gallo', 'Domenico', 'Bari', '1980', 'Vito', 'Rosa')
            ]
            
            inserted_count = 0
            for persona in persone_da_inserire:
                cur.execute("SELECT id FROM persone WHERE cognome = %s AND nome = %s AND data_nascita = %s", (persona[0], persona[1], persona[3]))
                exists = cur.fetchone()
                
                if not exists:
                    cur.execute("""
                        INSERT INTO persone (cognome, nome, luogo_nascita, data_nascita, nome_padre, nome_madre) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, persona)
                    inserted_count += 1

        conn.commit()
        conn.close()
        
        if inserted_count > 0:
            msg = f"Setup completato! Aggiunti {inserted_count} nuovi record."
        else:
            msg = "Setup non necessario. Nessun nuovo dato da aggiungere."

        return f"<h1>{msg}</h1>"
    except Exception as e:
        return f"<h1>Errore durante il setup!</h1><p>{e}</p>"

# --- ROTTA DI DEBUG (invariata) ---
@app.route('/debug-db')
def debug_db():
    # ... (codice invariato)
    pass

# --- NUOVA ROTTA PER CARICARE IL CSV ---
@app.route('/upload', methods=['POST'])
def upload_csv():
    """Gestisce l'upload di un file CSV e inserisce i dati nel database."""
    if 'csv_file' not in request.files:
        flash('Nessun file selezionato nel form.', 'warning')
        return redirect(url_for('index'))
    
    file = request.files['csv_file']
    
    if file.filename == '':
        flash('Nessun file selezionato.', 'warning')
        return redirect(url_for('index'))
        
    if file and file.filename.endswith('.csv'):
        try:
            # Legge il file in memoria come testo, decodificandolo in UTF-8
            stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
            csv_reader = csv.reader(stream)
            
            conn = get_db_connection()
            with conn.cursor() as cur:
                inserted_count = 0
                skipped_count = 0
                for row in csv_reader:
                    if not row: continue # Salta righe vuote
                    if len(row) != 6:
                        skipped_count += 1
                        continue 

                    cognome, nome, luogo_nascita, data_nascita, nome_padre, nome_madre = row
                    
                    cur.execute("SELECT id FROM persone WHERE cognome = %s AND nome = %s AND data_nascita = %s", (cognome, nome, data_nascita))
                    exists = cur.fetchone()

                    if not exists:
                        cur.execute("""
                            INSERT INTO persone (cognome, nome, luogo_nascita, data_nascita, nome_padre, nome_madre) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (cognome.strip(), nome.strip(), luogo_nascita.strip(), data_nascita.strip(), nome_padre.strip(), nome_madre.strip()))
                        inserted_count += 1
                    else:
                        skipped_count += 1
            
            conn.commit()
            conn.close()
            flash(f'Caricamento completato! Record inseriti: {inserted_count}. Record saltati (duplicati o malformati): {skipped_count}.', 'success')
        except Exception as e:
            flash(f'Errore critico durante il caricamento del file CSV: {e}', 'danger')
        
        return redirect(url_for('index'))

    else:
        flash('Formato file non valido. Si prega di caricare un file .csv.', 'danger')
        return redirect(url_for('index'))


# --- ROTTA PRINCIPALE DELL'APPLICAZIONE (invariata) ---
@app.route("/", methods=["GET", "POST"])
def index():
    # ... (tutto il resto del codice della funzione index rimane identico)
    per_page = request.args.get("per_page", DEFAULT_RESULTS_PER_PAGE, type=int)
    if per_page not in [10, 20, 50]:
        per_page = DEFAULT_RESULTS_PER_PAGE

    page = request.args.get("page", 1, type=int)
    risultati = []
    total_pages = 0
    total_results = 0
    validation_error = None
    start_result = 0
    end_result = 0
    is_search_active = False

    total_record_count = get_total_record_count()
    last_update_date = "N/D"

    search_params = {
        'cognome_testo': '', 'cognome_tipo': 'inizia',
        'nome_testo': '', 'nome_tipo': 'inizia',
        'data_nascita_anno': '', 'data_nascita_tipo': 'anno_esatto',
        'nome_padre_testo': '', 'nome_padre_tipo': 'inizia',
        'nome_madre_testo': '', 'nome_madre_tipo': 'inizia',
        'sort_by': 'cognome',
        'sort_order': 'asc',
        'per_page': per_page,
        'letter': ''
    }

    request_source = request.form if request.method == 'POST' else request.args
    for key in search_params:
        if key in request_source:
            if key == 'per_page':
                search_params[key] = int(request_source[key])
            else:
                search_params[key] = request_source[key]

    if request.method == 'POST':
        page = 1
        search_params['letter'] = ''
    
    if request.args.get('letter'):
        page = 1

    where_clauses = []
    query_params = []
    
    field_map = {
        'cognome': ('cognome_testo', 'cognome_tipo'), 'nome': ('nome_testo', 'nome_tipo'),
        'nome_padre': ('nome_padre_testo', 'nome_padre_tipo'), 'nome_madre': ('nome_madre_testo', 'nome_madre_tipo'),
    }
    active_fields = {}
    for db_col, (testo_key, _) in field_map.items():
        testo = search_params.get(testo_key, '').strip()
        if testo: active_fields[db_col] = testo
    
    anno_nascita = search_params.get('data_nascita_anno', '').strip()
    if anno_nascita: active_fields['data_nascita'] = anno_nascita

    is_search_active = bool(active_fields) or bool(search_params.get('letter'))

    if is_search_active:
        invalid_fields = []
        for label, text in active_fields.items():
            if label != 'data_nascita' and len(text) < 3: invalid_fields.append(label)
        if 'data_nascita' in active_fields and not (len(active_fields['data_nascita']) == 4 and active_fields['data_nascita'].isdigit()):
            invalid_fields.append('data_nascita')

        if invalid_fields:
            field_labels = {'cognome': 'Cognome', 'nome': 'Nome', 'data_nascita': 'Anno di Nascita (deve essere di 4 cifre)', 'nome_padre': 'Nome del Padre', 'nome_madre': 'Nome della Madre'}
            invalid_labels = [field_labels[key] for key in invalid_fields]
            validation_error = f"I seguenti campi non sono validi: {', '.join(invalid_labels)}."
        else:
            for db_col, testo in active_fields.items():
                if db_col == 'data_nascita': continue
                _, tipo_key = field_map[db_col]
                tipo = search_params.get(tipo_key, 'inizia')
                if tipo == "esatto": filtro = testo
                elif tipo == "inizia": filtro = f"{testo}%"
                else: filtro = f"%{testo}%"
                where_clauses.append(f"{db_col} ILIKE %s")
                query_params.append(filtro)

            if 'data_nascita' in active_fields:
                anno = int(active_fields['data_nascita'])
                tipo_anno = search_params.get('data_nascita_tipo', 'anno_esatto')
                if tipo_anno == 'anno_esatto':
                    where_clauses.append("data_nascita = %s")
                    query_params.append(str(anno))
                elif tipo_anno == 'pm_1':
                    where_clauses.append("CAST(data_nascita AS INTEGER) BETWEEN %s AND %s")
                    query_params.extend([anno - 1, anno + 1])
                elif tipo_anno == 'pm_5':
                    where_clauses.append("CAST(data_nascita AS INTEGER) BETWEEN %s AND %s")
                    query_params.extend([anno - 5, anno + 5])
            
            if search_params['letter']:
                where_clauses.append("cognome ILIKE %s")
                query_params.append(f"{search_params['letter']}%")

    if is_search_active and not validation_error and where_clauses:
        sql_where_string = " AND ".join(where_clauses)
        count_query = f"SELECT COUNT(*) FROM persone WHERE {sql_where_string}"
        total_results = count_query_db(count_query, tuple(query_params))
        total_pages = math.ceil(total_results / per_page)
        offset = (page - 1) * per_page
        
        start_result = min(offset + 1, total_results)
        end_result = min(offset + per_page, total_results)

        sort_by_col = search_params['sort_by']
        sort_order = search_params['sort_order'].upper()
        if sort_by_col not in ['cognome', 'nome', 'data_nascita'] or sort_order not in ['ASC', 'DESC']:
            sort_by_col, sort_order = 'cognome', 'ASC'
        order_by_clause = f"ORDER BY {sort_by_col} {sort_order}"

        data_query = f"SELECT * FROM persone WHERE {sql_where_string