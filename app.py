import json
import os
import re as _re
import sqlite3
import threading
import webbrowser
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, jsonify, render_template, request, Response

import comparator
import data_loader
import executor

app = Flask(__name__)


# ---------------------------------------------------------------------------
# HTTP Basic Auth (activée si APP_PASSWORD est défini dans l'environnement)
# ---------------------------------------------------------------------------

def _check_auth(username, password):
    return (username == os.environ.get('APP_USER', 'admin') and
            password == os.environ.get('APP_PASSWORD', ''))

@app.before_request
def require_auth():
    if not os.environ.get('APP_PASSWORD'):
        return  # pas de mot de passe défini → usage local, pas d'auth
    auth = request.authorization
    if not auth or not _check_auth(auth.username, auth.password):
        return Response(
            'Accès refusé. Identifiez-vous.',
            401,
            {'WWW-Authenticate': 'Basic realm="DA Interview Prep"'},
        )


@app.template_filter('md')
def md_filter(text):
    """Minimal markdown: backticks → <code>, **bold** → <strong>, newlines → <br>."""
    text = _re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = _re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = text.replace('\n', '<br>')
    return text

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'data', 'practice.db')
PROGRESS_DB = os.path.join(BASE_DIR, 'data', 'progress.db')

QUESTIONS = {}
EXPECTED = {}
DATAFRAMES = {}


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------

def load_questions():
    cats = ['sql', 'pandas', 'theory']
    for cat in cats:
        path = os.path.join(BASE_DIR, 'questions', f'{cat}.json')
        with open(path, encoding='utf-8') as f:
            QUESTIONS[cat] = json.load(f)


def compute_expected():
    for q in QUESTIONS.get('sql', []):
        EXPECTED[q['id']] = executor.run_sql(q['solution_code'], DB_PATH)

    for q in QUESTIONS.get('pandas', []):
        EXPECTED[q['id']] = executor.run_pandas(q['solution_code'], DATAFRAMES)


def init_progress_db():
    conn = sqlite3.connect(PROGRESS_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS question_status (
            question_id TEXT PRIMARY KEY,
            category    TEXT NOT NULL,
            difficulty  TEXT NOT NULL,
            status      TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_progress_map():
    """Returns {question_id: status} where status in ('passed', 'failed', 'retry')."""
    conn = sqlite3.connect(PROGRESS_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT question_id, status FROM question_status").fetchall()
    conn.close()
    return {r['question_id']: r['status'] for r in rows}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    progress = get_progress_map()
    stats = {}
    for cat, qs in QUESTIONS.items():
        total = len(qs)
        passed = sum(1 for q in qs if progress.get(q['id']) == 'passed')
        attempted = sum(1 for q in qs if q['id'] in progress)
        stats[cat] = {
            'total': total,
            'attempted': attempted,
            'passed': passed,
            'pct': round(passed / total * 100) if total else 0,
        }
    return render_template('index.html', stats=stats)


@app.route('/questions/<category>')
def question_list(category):
    if category not in QUESTIONS:
        return 'Catégorie inconnue', 404
    qs = QUESTIONS[category]
    progress = get_progress_map()
    filter_mode = request.args.get('filter', 'all')

    if filter_mode == 'not_attempted':
        qs = [q for q in qs if q['id'] not in progress]
    elif filter_mode == 'passed':
        qs = [q for q in qs if progress.get(q['id']) == 'passed']
    elif filter_mode == 'retry':
        qs = [q for q in qs if progress.get(q['id']) == 'retry']

    return render_template('question_list.html',
                           category=category,
                           questions=qs,
                           progress=progress,
                           filter_mode=filter_mode)


@app.route('/question/<category>/<question_id>')
def question_view(category, question_id):
    qs = QUESTIONS.get(category, [])
    q = next((x for x in qs if x['id'] == question_id), None)
    if not q:
        return 'Question introuvable', 404

    progress = get_progress_map()
    current_status = progress.get(question_id)  # 'passed'/'failed'/'retry'/None

    idx = next(i for i, x in enumerate(qs) if x['id'] == question_id)
    prev_id = qs[idx - 1]['id'] if idx > 0 else None
    next_id = qs[idx + 1]['id'] if idx < len(qs) - 1 else None

    if category == 'theory':
        return render_template('question_theory.html',
                               q=q, category=category,
                               current_status=current_status,
                               prev_id=prev_id, next_id=next_id)
    else:
        setup_note = q.get('setup_note', '')
        if category == 'sql':
            tables_info = _get_tables_info()
            setup_note += '\n\n' + tables_info
        return render_template('question_code.html',
                               q=q, category=category,
                               current_status=current_status,
                               prev_id=prev_id, next_id=next_id,
                               setup_note=setup_note)


@app.route('/run', methods=['POST'])
def run_code():
    data = request.get_json()
    category = data.get('category')
    code = data.get('code', '')

    if category == 'sql':
        result = executor.run_sql(code, DB_PATH)
    elif category == 'pandas':
        result = executor.run_pandas(code, DATAFRAMES)
    else:
        return jsonify({'error': 'Catégorie inconnue'}), 400

    return jsonify(result)


@app.route('/check', methods=['POST'])
def check_answer():
    data = request.get_json()
    category = data.get('category')
    question_id = data.get('question_id')
    code = data.get('code', '')

    q = next((x for x in QUESTIONS.get(category, []) if x['id'] == question_id), None)
    if not q:
        return jsonify({'error': 'Question introuvable'}), 404

    if category == 'sql':
        user_result = executor.run_sql(code, DB_PATH)
    elif category == 'pandas':
        user_result = executor.run_pandas(code, DATAFRAMES)
    else:
        return jsonify({'error': 'Catégorie inconnue'}), 400

    expected = EXPECTED.get(question_id, {})
    ordered = q.get('ordered', False)
    comparison = comparator.compare_results(user_result, expected, ordered=ordered)
    return jsonify(comparison)


@app.route('/solution/<category>/<question_id>')
def get_solution(category, question_id):
    q = next((x for x in QUESTIONS.get(category, []) if x['id'] == question_id), None)
    if not q:
        return jsonify({'error': 'Question introuvable'}), 404
    return jsonify({
        'solution_code': q.get('solution_code', ''),
        'solution_text': q.get('solution_text', ''),
        'explanation': q.get('explanation', ''),
        'key_points': q.get('key_points', []),
    })


@app.route('/progress', methods=['POST'])
def record_progress():
    data = request.get_json()
    question_id = data.get('question_id')
    category = data.get('category')
    status = data.get('status')  # 'passed', 'failed', 'retry', or None to delete

    q = next((x for x in QUESTIONS.get(category, []) if x['id'] == question_id), None)
    difficulty = q['difficulty'] if q else 'unknown'

    conn = sqlite3.connect(PROGRESS_DB)
    if status is None:
        conn.execute("DELETE FROM question_status WHERE question_id = ?", (question_id,))
    else:
        conn.execute("""
            INSERT INTO question_status (question_id, category, difficulty, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(question_id) DO UPDATE SET
                status     = excluded.status,
                updated_at = excluded.updated_at
        """, (question_id, category, difficulty, status, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.route('/stats')
def stats():
    conn = sqlite3.connect(PROGRESS_DB)
    conn.row_factory = sqlite3.Row

    all_statuses = conn.execute("""
        SELECT question_id, category, difficulty, status, updated_at
        FROM question_status
        ORDER BY updated_at DESC
    """).fetchall()

    # Timeline (last 15 by updated_at)
    timeline = all_statuses[:15]

    conn.close()

    by_category = {}
    by_difficulty = {}
    overall_passed = 0

    for row in all_statuses:
        cat = row['category']
        diff = row['difficulty']
        s = row['status']

        if cat not in by_category:
            by_category[cat] = {'passed': 0, 'retry': 0, 'total': 0}
        by_category[cat]['total'] += 1
        by_category[cat][s] = by_category[cat].get(s, 0) + 1
        if s == 'passed':
            overall_passed += 1

        if diff not in by_difficulty:
            by_difficulty[diff] = {'passed': 0, 'retry': 0, 'total': 0}
        by_difficulty[diff]['total'] += 1
        by_difficulty[diff][s] = by_difficulty[diff].get(s, 0) + 1

    total_questions = sum(len(v) for v in QUESTIONS.values())
    attempted_questions = len(all_statuses)
    total_attempts = attempted_questions  # kept for template compat

    for cat in QUESTIONS:
        if cat not in by_category:
            by_category[cat] = {'passed': 0, 'retry': 0, 'total': 0}
        by_category[cat]['total_questions'] = len(QUESTIONS[cat])
        t = by_category[cat]['total']
        by_category[cat]['pct'] = round(by_category[cat]['passed'] / t * 100) if t else 0

    for diff in by_difficulty:
        t = by_difficulty[diff]['total']
        by_difficulty[diff]['pct'] = round(by_difficulty[diff]['passed'] / t * 100) if t else 0

    timeline_data = []
    for row in timeline:
        qid = row['question_id']
        cat = row['category']
        q = next((x for x in QUESTIONS.get(cat, []) if x['id'] == qid), None)
        timeline_data.append({
            'question_id': qid,
            'category': cat,
            'title': q['title'] if q else qid,
            'status': row['status'],
            'updated_at': row['updated_at'][:16].replace('T', ' '),
        })

    return render_template('stats.html',
                           total_questions=total_questions,
                           attempted_questions=attempted_questions,
                           overall_passed=overall_passed,
                           by_category=by_category,
                           by_difficulty=by_difficulty,
                           timeline=timeline_data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_tables_info():
    conn = sqlite3.connect(DB_PATH)
    lines = []
    for table in ['customers', 'products', 'orders', 'employees', 'monthly_sales']:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        # PK columns (pk > 0)
        col_info = conn.execute(f"PRAGMA table_info({table})").fetchall()
        pk_cols = {row[1] for row in col_info if row[5] > 0}

        # FK columns: from_col → referenced_table
        fk_info = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
        fk_map = {row[3]: row[2] for row in fk_info}  # {from_col: ref_table}

        col_parts = []
        for row in col_info:
            name = row[1]
            if name in pk_cols:
                col_parts.append(f"`{name}` PK")
            elif name in fk_map:
                col_parts.append(f"`{name}` FK→{fk_map[name]}")
            else:
                col_parts.append(f"`{name}`")

        lines.append(f"- **{table}** ({count} lignes) : {', '.join(col_parts)}")
    conn.close()
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Initialisation (appelée en local ET par le serveur WSGI)
# ---------------------------------------------------------------------------

def _init():
    data_loader.initialize()
    DATAFRAMES.update(data_loader.get_dataframes())
    load_questions()
    compute_expected()
    init_progress_db()
    total = sum(len(v) for v in QUESTIONS.values())
    print(f"DA Interview Prep prêt — {total} questions chargées.")


_init()


# ---------------------------------------------------------------------------
# Entry point local
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    threading.Timer(1.0, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
