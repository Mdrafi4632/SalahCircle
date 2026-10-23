from flask import Flask, render_template, request, redirect, url_for, session
import requests
import os
from datetime import date

app = Flask(__name__, static_folder='static')
app.secret_key = 'prayer-tracker-secret-2024'

API_URL = os.environ.get('API_URL', 'http://localhost:5001')
PRAYER_API_CITY = 'New York'
PRAYER_API_COUNTRY = 'US'


def get_prayer_times():
    try:
        from datetime import date
        today = date.today()
        url = f"http://api.aladhan.com/v1/timingsByCity/{today.day}-{today.month}-{today.year}"
        resp = requests.get(url, params={
            'city': PRAYER_API_CITY,
            'country': PRAYER_API_COUNTRY,
            'method': 2
        }, timeout=5)
        data = resp.json()
        timings = data['data']['timings']
        return {
            'Fajr': timings['Fajr'],
            'Dhuhr': timings['Dhuhr'],
            'Asr': timings['Asr'],
            'Maghrib': timings['Maghrib'],
            'Isha': timings['Isha']
        }
    except Exception:
        return {
            'Fajr': '--:--', 'Dhuhr': '--:--', 'Asr': '--:--',
            'Maghrib': '--:--', 'Isha': '--:--'
        }


@app.route('/')
def index():
    user_id = session.get('user_id')
    user_name = session.get('user_name')

    users_resp = requests.get(f'{API_URL}/api/users')
    users = users_resp.json()

    prayer_times = get_prayer_times()

    if user_id:
        prayers_resp = requests.get(f'{API_URL}/api/prayers/{user_id}/today')
        prayers = prayers_resp.json()
        social_resp = requests.get(f'{API_URL}/api/social/today')
        social = social_resp.json()
    else:
        prayers = []
        social = []

    motivation = ""
    if user_id:
       try:
           mot_resp = requests.get(f'{API_URL}/api/motivation/{user_id}', timeout=8)
           motivation = mot_resp.json().get('message', '') or "Alhamdulillah, keep striving! Every prayer brings you closer to Allah. 🤲"
       except:
           motivation = "Alhamdulillah, keep striving! Every prayer brings you closer to Allah. 🤲"

    today_date = date.today().strftime('%A, %B %d, %Y')

    return render_template('index.html',
                           user_id=user_id,
                           user_name=user_name,
                           users=users,
                           prayers=prayers,
                           social=social,
                           prayer_times=prayer_times,
                           motivation=motivation,
                           today_date=today_date)


@app.route('/join', methods=['POST'])
def join():
    name = request.form.get('name', '').strip()
    if name:
        resp = requests.post(f'{API_URL}/api/users', json={'name': name})
        data = resp.json()
        session['user_id'] = data['id']
        session['user_name'] = data['name']
    return redirect(url_for('index'))


@app.route('/switch/<int:user_id>')
def switch_user(user_id):
    resp = requests.get(f'{API_URL}/api/users')
    users = resp.json()
    for u in users:
        if u['id'] == user_id:
            session['user_id'] = u['id']
            session['user_name'] = u['name']
            break
    return redirect(url_for('index'))


@app.route('/toggle/<prayer_name>')
def toggle(prayer_name):
    user_id = session.get('user_id')
    if user_id:
        requests.post(f'{API_URL}/api/prayers/{user_id}/toggle',
                      json={'prayer_name': prayer_name})
    return redirect(url_for('index'))


@app.route('/analytics')
def analytics():
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    if not user_id:
        return redirect(url_for('index'))
    resp = requests.get(f'{API_URL}/api/analytics/{user_id}')
    data = resp.json()
    return render_template('analytics.html',
                           user_name=user_name,
                           user_id=user_id,
                           analytics=data)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/delete-user/<int:user_id>')
def delete_user(user_id):
    requests.delete(f'{API_URL}/api/users/{user_id}')
    if session.get('user_id') == user_id:
        session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
