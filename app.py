from flask import Flask, request, render_template
import sqlite3
import math
import os
from datetime import datetime

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.do')

DEFAULT_RESULTS_PER_PAGE = 20
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def normalize_date_for_sort(date_str):
    if not date_str: return "9999"
    try:
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                return f"{year:04d}{month:02d}{day:02d}"
        elif len(date_str) == 4 and date_str.isdigit():
            year = int(date_str)
            return f"{year:04d}0000"
        return "9999"
    except (ValueError, IndexError):
        return "9999"

def query_db(query, params=()):
    conn = sqlite3.connect("database.db")
    conn.create_function("normalize_date", 1, normalize_date_for_sort)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def count_query_db(query, params=()):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_record_count():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM persone")
        count = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        count = 0
    conn.close()
    return count

@app.route("/", methods=["GET", "POST"])
def index():
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
    last_update_date = ""
    try:
        timestamp = os.path.getmtime('database.db')
        last_update_date = datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y')
    except FileNotFoundError:
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
                where_clauses.append(f"{db_col} LIKE ?")
                query_params.append(filtro)

            if 'data_nascita' in active_fields:
                anno = int(active_fields['data_nascita'])
                tipo_anno = search_params.get('data_nascita_tipo', 'anno_esatto')
                if tipo_anno == 'anno_esatto':
                    where_clauses.append("data_nascita = ?")
                    query_params.append(str(anno))
                elif tipo_anno == 'pm_1':
                    where_clauses.append("CAST(data_nascita AS INTEGER) BETWEEN ? AND ?")
                    query_params.extend([anno - 1, anno + 1])
                elif tipo_anno == 'pm_5':
                    where_clauses.append("CAST(data_nascita AS INTEGER) BETWEEN ? AND ?")
                    query_params.extend([anno - 5, anno + 5])
            
            # Aggiunge il filtro per lettera se presente
            if search_params['letter']:
                where_clauses.append("cognome LIKE ?")
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
        if sort_by_col == 'data_nascita':
            order_by_clause = f"ORDER BY normalize_date(data_nascita) {sort_order}"
        else:
            order_by_clause = f"ORDER BY {sort_by_col} {sort_order}"

        data_query = f"SELECT * FROM persone WHERE {sql_where_string} {order_by_clause} LIMIT ? OFFSET ?"
        final_params = tuple(query_params) + (per_page, offset)
        risultati = query_db(data_query, final_params)

    return render_template(
        "index.html",
        risultati=risultati,
        page=page,
        total_pages=total_pages,
        total_results=total_results,
        search_params=search_params,
        validation_error=validation_error,
        total_record_count=total_record_count,
        last_update_date=last_update_date,
        start_result=start_result,
        end_result=end_result,
        alphabet=ALPHABET,
        is_search_active=is_search_active
    )

if __name__ == "__main__":
    app.run(debug=True)
