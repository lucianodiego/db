# -*- coding: utf-8 -*-

# Import delle librerie necessarie
import os
import psycopg2
from psycopg2.extras import DictCursor, execute_values
import math
from flask import Flask, request, render_template, flash, redirect, url_for
from datetime import datetime
import csv
import io
import sys
import re

# --- Configurazione Iniziale ---
app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.do') 
app.secret_key = os.environ.get('SECRET_KEY', 'una-chiave-segreta-molto-sicura-per-test-locali')

DEFAULT_RESULTS_PER_PAGE = 20
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# --- Funzioni Helper e Filtri Jinja ---
def format_display_date(date_str):
    """Filtro per Jinja2: mostra 'Disponibile*' se la data contiene lettere."""
    if not date_str or any(c.isalpha() for c in str(date_str)):
        return "Disponibile*"
    return date_str

app.jinja_env.filters['format_date'] = format_display_date

# --- Funzioni di Connessione al Database ---
def get_db_connection():
    """Crea una connessione al database PostgreSQL su Render."""
    conn_url = os.environ.get('DATABASE_URL')
    if not conn_url:
        raise RuntimeError("DATABASE_URL non è impostata. Assicurati di averla aggiunta su Render.")
    conn = psycopg2.connect(conn_url)
    return conn

# --- Rotte dell'Applicazione ---

@app.route('/setup-database-online-super-segreto-12345')
def setup_online_db():
    """
    Questa rotta assicura che le tabelle necessarie esistano.
    È sicura e veloce da eseguire più volte.
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
            cur.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key VARCHAR(50) PRIMARY KEY,
                value VARCHAR(255)
            );
            """)
            cur.execute("""
                INSERT INTO metadata (key, value) VALUES ('last_update', 'Database non ancora popolato')
                ON CONFLICT (key) DO NOTHING;
            """)
        conn.commit()
        conn.close()
        msg = "Setup di verifica completato! Le tabelle del database sono state create o verificate con successo."
        return f"<h1>{msg}</h1>"
    except Exception as e:
        return f"<h1>Errore durante il setup!</h1><p>{e}</p>"

@app.route('/upload', methods=['POST'])
def upload_csv():
    """Gestisce l'upload di un file CSV con un metodo di inserimento massivo (bulk insert)."""
    if 'csv_file' not in request.files:
        flash('Nessun file selezionato nel form.', 'warning')
        return redirect(url_for('index'))
    
    file = request.files['csv_file']
    
    if file.filename == '':
        flash('Nessun file selezionato.', 'warning')
        return redirect(url_for('index'))
        
    if file and file.filename.endswith('.csv'):
        csv.field_size_limit(512 * 1024)
        file_bytes = file.stream.read()
        decoded_content = None
        try:
            decoded_content = file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                decoded_content = file_bytes.decode('latin-1')
            except UnicodeDecodeError:
                flash("Impossibile decodificare il file. Prova a salvarlo con codifica UTF-8.", 'danger')
                return redirect(url_for('index'))

        try:
            stream = io.StringIO(decoded_content)
            dialect = csv.Sniffer().sniff(stream.read(2048), delimiters=',;')
            stream.seek(0)
            csv_reader = csv.reader(stream, dialect)
            
            records_to_insert = [tuple(field.strip() for field in row) for row in csv_reader if row and len(row) == 6]
            
            if records_to_insert:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    cur.execute("TRUNCATE TABLE persone RESTART IDENTITY;")
                    execute_values(cur, 
                        "INSERT INTO persone (cognome, nome, luogo_nascita, data_nascita, nome_padre, nome_madre) VALUES %s",
                        records_to_insert)
                    now_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    cur.execute("INSERT INTO metadata (key, value) VALUES ('last_update', %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;", (now_str,))
                conn.commit()
                conn.close()
                flash(f'Caricamento completato! Inseriti {len(records_to_insert)} nuovi record.', 'success')
            else:
                flash('Nessun record valido trovato nel file CSV.', 'warning')
        except Exception as e:
            flash(f'Errore critico durante l\'elaborazione del file CSV: {e}', 'danger')
        
        return redirect(url_for('index'))
    else:
        flash('Formato file non valido. Si prega di caricare un file .csv.', 'danger')
        return redirect(url_for('index'))

@app.route("/", methods=["GET", "POST"])
def index():
    per_page = request.args.get("per_page", DEFAULT_RESULTS_PER_PAGE, type=int)
    if per_page not in [10, 20, 50]: per_page = DEFAULT_RESULTS_PER_PAGE
    page = request.args.get("page", 1, type=int)

    search_params = {
        'cognome_testo': '', 'cognome_tipo': 'inizia',
        'nome_testo': '', 'nome_tipo': 'inizia',
        'data_nascita_anno': '', 'data_nascita_tipo': 'anno_esatto',
        'nome_padre_testo': '', 'nome_padre_tipo': 'inizia',
        'nome_madre_testo': '', 'nome_madre_tipo': 'inizia',
        'sort_by': 'cognome', 'sort_order': 'asc',
        'per_page': per_page, 'letter': ''
    }
    request_source = request.form if request.method == 'POST' else request.args
    for key in search_params:
        if key in request_source: search_params[key] = request_source[key]
    if request.method == 'POST': page = 1; search_params['letter'] = ''
    if request.args.get('letter'): page = 1

    where_clauses, query_params, validation_error = [], [], None
    field_map = {'cognome': 'cognome_testo', 'nome': 'nome_testo', 'nome_padre': 'nome_padre_testo', 'nome_madre': 'nome_madre_testo'}
    
    for db_col, form_field in field_map.items():
        testo = search_params.get(form_field, '').strip()
        if testo:
            if len(testo) < 3: validation_error = "I campi di testo devono contenere almeno 3 caratteri."; break
            tipo = search_params.get(f"{form_field.replace('_testo', '_tipo')}", 'inizia')
            filtro = f"{testo}%" if tipo == 'inizia' else f"%{testo}%" if tipo == 'contiene' else testo
            where_clauses.append(f"{db_col} ILIKE %s")
            query_params.append(filtro)

    anno_nascita = search_params.get('data_nascita_anno', '').strip()
    if anno_nascita:
        if not (len(anno_nascita) == 4 and anno_nascita.isdigit()): validation_error = "L'anno di nascita deve essere di 4 numeri."
        else:
            anno = int(anno_nascita)
            tipo_anno = search_params.get('data_nascita_tipo', 'anno_esatto')
            if tipo_anno == 'anno_esatto': where_clauses.append("SUBSTRING(data_nascita, '....$') = %s"); query_params.append(str(anno))
            elif tipo_anno == 'pm_1': where_clauses.append("CAST(SUBSTRING(data_nascita, '....$') AS INTEGER) BETWEEN %s AND %s"); query_params.extend([anno - 1, anno + 1])
            elif tipo_anno == 'pm_5': where_clauses.append("CAST(SUBSTRING(data_nascita, '....$') AS INTEGER) BETWEEN %s AND %s"); query_params.extend([anno - 5, anno + 5])

    if search_params.get('letter'): where_clauses.append("cognome ILIKE %s"); query_params.append(f"{search_params['letter']}%")
    
    is_search_active = bool(where_clauses)
    risultati, total_results, total_pages, start_result, end_result = [], 0, 0, 0, 0

    if is_search_active and not validation_error:
        sql_where_string = " AND ".join(where_clauses)
        count_query = f"SELECT COUNT(*) FROM persone WHERE {sql_where_string}"
        total_results = count_query_db(count_query, tuple(query_params))
        total_pages = math.ceil(total_results / per_page) if total_results > 0 else 0

        sort_by_col, sort_order = search_params['sort_by'], 'DESC' if search_params['sort_order'] == 'desc' else 'ASC'
        order_by_clause = f"ORDER BY {sort_by_col} {sort_order} NULLS LAST"
        if sort_by_col == 'data_nascita':
            order_by_clause = f"""ORDER BY
                to_date(
                    CASE WHEN data_nascita ~ '^[0-9]{{1,2}}/[0-9]{{1,2}}/[0-9]{{4}}$' THEN data_nascita
                         WHEN data_nascita ~ '^[0-9]{{4}}$' THEN '01/01/' || data_nascita
                         ELSE '01/01/9999' END,
                    'DD/MM/YYYY'
                ) {sort_order} NULLS LAST
            """
        
        offset = (page - 1) * per_page
        data_query = f"SELECT * FROM persone WHERE {sql_where_string} {order_by_clause} LIMIT %s OFFSET %s"
        risultati = query_db(data_query, tuple(query_params) + (per_page, offset))
        start_result, end_result = min(offset + 1, total_results), min(offset + per_page, total_results)

    total_record_count = get_total_record_count()
    last_update_date = "N/D"
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT value FROM metadata WHERE key = 'last_update'")
            record = cur.fetchone()
            if record: last_update_date = record['value']
        conn.close()
    except Exception: pass

    return render_template("index.html", risultati=risultati, page=page, total_pages=total_pages,
                           total_results=total_results, search_params=search_params, validation_error=validation_error,
                           total_record_count=total_record_count, last_update_date=last_update_date,
                           start_result=start_result, end_result=end_result, alphabet=ALPHABET, is_search_active=is_search_active)

if __name__ == "__main__":
    app.run(debug=True)
