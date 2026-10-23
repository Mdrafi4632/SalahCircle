from flask import Flask, request, jsonify, g
import sqlite3
from datetime import date, timedelta
import os
import google.generativeai as genai

genai.configure(api_key="AIzaSyC5505lJ1IULQafsRRsQ6FL9k-A4_FASzM")

DATABASE = 'prayer.db'

app = Flask(__name__)
app.config['DATABASE'] = DATABASE


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        g.sqlite_db.row_factory = sqlite3.Row
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS prayers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            prayer_name TEXT NOT NULL,
            prayer_date TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, prayer_name, prayer_date)
        );
    ''')
    db.commit()
    db.close()


PRAYERS = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']



@app.route('/api/users', methods=['GET'])
def get_users():
    db = get_db()
    rows = db.execute('SELECT id, name, created_at FROM users ORDER BY name').fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.get_json()
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    db = get_db()
    try:
        db.execute('INSERT INTO users (name) VALUES (?)', (name,))
        db.commit()
        row = db.execute('SELECT id, name FROM users WHERE name = ?', (name,)).fetchone()
        return jsonify(dict(row)), 201
    except sqlite3.IntegrityError:
        row = db.execute('SELECT id, name FROM users WHERE name = ?', (name,)).fetchone()
        return jsonify(dict(row)), 200



@app.route('/api/prayers/<int:user_id>/today', methods=['GET'])
def get_today_prayers(user_id):
    today = str(date.today())
    db = get_db()
    # Ensure rows exist for today
    for p in PRAYERS:
        db.execute(
            'INSERT OR IGNORE INTO prayers (user_id, prayer_name, prayer_date, completed) VALUES (?, ?, ?, 0)',
            (user_id, p, today)
        )
    db.commit()
    rows = db.execute(
        'SELECT prayer_name, completed, completed_at FROM prayers WHERE user_id=? AND prayer_date=? ORDER BY id',
        (user_id, today)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/prayers/<int:user_id>/toggle', methods=['POST'])
def toggle_prayer(user_id):
    data = request.get_json()
    prayer_name = data.get('prayer_name')
    today = str(date.today())
    db = get_db()
    row = db.execute(
        'SELECT id, completed FROM prayers WHERE user_id=? AND prayer_name=? AND prayer_date=?',
        (user_id, prayer_name, today)
    ).fetchone()
    if not row:
        return jsonify({'error': 'Prayer not found'}), 404
    new_val = 0 if row['completed'] else 1
    completed_at = str(date.today()) if new_val else None
    db.execute(
        'UPDATE prayers SET completed=?, completed_at=? WHERE id=?',
        (new_val, completed_at, row['id'])
    )
    db.commit()
    return jsonify({'completed': new_val})



@app.route('/api/social/today', methods=['GET'])
def social_today():
    today = str(date.today())
    db = get_db()
    users = db.execute('SELECT id, name FROM users ORDER BY name').fetchall()
    result = []
    for u in users:
        # ensure rows exist
        for p in PRAYERS:
            db.execute(
                'INSERT OR IGNORE INTO prayers (user_id, prayer_name, prayer_date, completed) VALUES (?, ?, ?, 0)',
                (u['id'], p, today)
            )
        db.commit()
        rows = db.execute(
            'SELECT prayer_name, completed FROM prayers WHERE user_id=? AND prayer_date=? ORDER BY id',
            (u['id'], today)
        ).fetchall()
        prayers = {r['prayer_name']: r['completed'] for r in rows}
        completed_count = sum(prayers.values())
        result.append({
            'user_id': u['id'],
            'name': u['name'],
            'prayers': prayers,
            'completed': completed_count,
            'total': 5
        })
    return jsonify(result)



@app.route('/api/analytics/<int:user_id>', methods=['GET'])
def get_analytics(user_id):
    db = get_db()
    # Last 30 days heatmap
    today = date.today()
    days_30 = [(today - timedelta(days=i)) for i in range(29, -1, -1)]

    heatmap = {}
    for p in PRAYERS:
        heatmap[p] = []
        for d in days_30:
            row = db.execute(
                'SELECT completed FROM prayers WHERE user_id=? AND prayer_name=? AND prayer_date=?',
                (user_id, p, str(d))
            ).fetchone()
            heatmap[p].append({'date': str(d), 'completed': row['completed'] if row else 0})

    # 7-day trend (total prayers per day)
    trend_7 = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        rows = db.execute(
            'SELECT SUM(completed) as total FROM prayers WHERE user_id=? AND prayer_date=?',
            (user_id, str(d))
        ).fetchone()
        trend_7.append({'date': str(d), 'day': d.strftime('%a')[0], 'total': rows['total'] or 0})

    # Streak
    streak = 0
    for i in range(0, 365):
        d = today - timedelta(days=i)
        row = db.execute(
            'SELECT SUM(completed) as total FROM prayers WHERE user_id=? AND prayer_date=?',
            (user_id, str(d))
        ).fetchone()
        if row and row['total'] == 5:
            streak += 1
        else:
            break

    return jsonify({'heatmap': heatmap, 'trend_7': trend_7, 'streak': streak})



@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db = get_db()
    db.execute('DELETE FROM prayers WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    return jsonify({'result': True})


@app.route('/api/motivation/<int:user_id>', methods=['GET'])
def get_motivation(user_id):
    today = str(date.today())
    db = get_db()
    rows = db.execute(
        'SELECT prayer_name, completed FROM prayers WHERE user_id=? AND prayer_date=?',
        (user_id, today)
    ).fetchall()

    completed = [r['prayer_name'] for r in rows if r['completed']]
    missed = [r['prayer_name'] for r in rows if not r['completed']]

    prompt = f"You are an Islamic motivation assistant. The user completed these prayers today: {', '.join(completed) or 'none'}."
    if missed:
        prompt += f" They missed: {', '.join(missed)}."
    prompt += " Give a short, warm, encouraging Islamic message in 2 sentences max. Use words like MashaAllah, Alhamdulillah naturally."

    try:
       model = genai.GenerativeModel('gemini-2.5-flash-lite')
       response = model.generate_content(prompt)
       message = response.text
    except Exception as e:
       print(f"Gemini error: {e}")
       message = "Alhamdulillah, keep striving to complete your prayers. Every step towards Allah is blessed."
    return jsonify({'message': message})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
