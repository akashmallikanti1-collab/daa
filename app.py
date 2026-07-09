from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json, os, uuid
from datetime import datetime
from matching import match_rides, dijkstra

app = Flask(__name__)
app.secret_key = 'vasavi_rideshare_secret_2024'
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "rides": [], "algo_traces": {}}
    with open(DATA_FILE) as f:
        d = json.load(f)
    if "algo_traces" not in d:
        d["algo_traces"] = {}
    return d


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


# ── Auth ──────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = load_data()
        name     = request.form['name'].strip()
        email    = request.form['email'].strip().lower()
        phone    = request.form['phone'].strip()
        password = request.form['password']
        if email in data['users']:
            return render_template('signup.html', error='Email already registered.')
        uid = str(uuid.uuid4())[:8]
        data['users'][email] = {
            'name': name, 'email': email, 'phone': phone,
            'password': password, 'id': uid,
            'bio': '', 'joined': datetime.now().strftime('%Y-%m-%d'),
        }
        save_data(data)
        session['user'] = {'email': email, 'name': name, 'phone': phone, 'id': uid}
        return redirect(url_for('dashboard'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data     = load_data()
        email    = request.form['email'].strip().lower()
        password = request.form['password']
        user     = data['users'].get(email)
        if user and user['password'] == password:
            session['user'] = {
                'email': email, 'name': user['name'],
                'phone': user['phone'], 'id': user['id']
            }
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid email or password.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ── Profile ───────────────────────────────────────────────────────

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    data     = load_data()
    user_rec = data['users'].get(session['user']['email'], {})
    error = success = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_info':
            user_rec['name']  = request.form['name'].strip()
            user_rec['phone'] = request.form['phone'].strip()
            user_rec['bio']   = request.form.get('bio', '').strip()
            session['user']['name']  = user_rec['name']
            session['user']['phone'] = user_rec['phone']
            save_data(data)
            success = 'Profile updated!'
        elif action == 'change_password':
            old_pw, new_pw, conf_pw = (request.form['old_password'],
                                       request.form['new_password'],
                                       request.form['confirm_password'])
            if user_rec['password'] != old_pw:
                error = 'Current password is incorrect.'
            elif new_pw != conf_pw:
                error = 'New passwords do not match.'
            elif len(new_pw) < 6:
                error = 'Password must be at least 6 characters.'
            else:
                user_rec['password'] = new_pw
                save_data(data)
                success = 'Password changed!'

    user_rides = [r for r in data['rides'] if r['user_id'] == session['user']['id']]
    stats = {
        'total':     len(user_rides),
        'matched':   sum(1 for r in user_rides if r['status'] == 'matched'),
        'searching': sum(1 for r in user_rides if r['status'] == 'searching'),
        'cancelled': sum(1 for r in user_rides if r['status'] == 'cancelled'),
        'given':     sum(1 for r in user_rides if r['type'] == 'give'),
        'requested': sum(1 for r in user_rides if r['type'] == 'request'),
    }
    return render_template('profile.html', user=session['user'],
                           user_rec=user_rec, stats=stats,
                           error=error, success=success)


# ── Dashboard — polls for new matches ────────────────────────────

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    data       = load_data()
    user_rides = [r for r in data['rides'] if r['user_id'] == session['user']['id']]
    user_rides.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('dashboard.html', user=session['user'], rides=user_rides)


# ── API: poll for match result (used by Laptop 1 / giver) ────────

@app.route('/api/check_match/<ride_id>')
def api_check_match(ride_id):
    """Laptop 1 polls this every 3 s to know if their ride got matched."""
    if 'user' not in session:
        return jsonify({'error': 'not logged in'}), 401
    data = load_data()
    ride = next((r for r in data['rides'] if r['id'] == ride_id), None)
    if not ride:
        return jsonify({'status': 'not_found'})
    if ride['status'] != 'matched':
        return jsonify({'status': ride['status']})
    # Find the partner ride
    partner = next((r for r in data['rides'] if r['id'] == ride.get('matched_with')), None)
    # Retrieve stored algo trace
    trace = data['algo_traces'].get(ride_id) or data['algo_traces'].get(ride.get('matched_with',''))
    return jsonify({
        'status': 'matched',
        'ride':    ride,
        'partner': partner,
        'algo_trace': trace,
    })


# ── Ride ─────────────────────────────────────────────────────────

@app.route('/ride', methods=['GET', 'POST'])
def ride():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data      = load_data()
        ride_type = request.form['ride_type']
        pickup    = request.form['pickup']
        dropoff   = request.form['dropoff']
        vehicle   = request.form['vehicle']
        seats     = int(request.form.get('seats', 1))

        new_ride = {
            'id':           str(uuid.uuid4())[:8],
            'user_id':      session['user']['id'],
            'user_name':    session['user']['name'],
            'user_phone':   session['user']['phone'],
            'user_email':   session['user']['email'],
            'type':         ride_type,
            'pickup':       pickup,
            'dropoff':      dropoff,
            'vehicle':      vehicle,
            'seats':        seats,
            'status':       'searching',
            'matched_with': None,
            'timestamp':    datetime.now().strftime('%Y-%m-%d %H:%M'),
        }

        match, algo_trace = match_rides(new_ride, data['rides'])

        if match:
            new_ride['status']       = 'matched'
            new_ride['matched_with'] = match['id']
            for r in data['rides']:
                if r['id'] == match['id']:
                    r['status']       = 'matched'
                    r['matched_with'] = new_ride['id']
                    break
            data['rides'].append(new_ride)
            # Store algo_trace keyed by BOTH ride ids so either user can fetch it
            data['algo_traces'][new_ride['id']]  = algo_trace
            data['algo_traces'][match['id']]      = algo_trace
            save_data(data)
            return render_template('result.html',
                                   user=session['user'],
                                   ride=new_ride, match=match,
                                   algo_trace=algo_trace, success=True)
        else:
            data['rides'].append(new_ride)
            save_data(data)
            # No match yet — show waiting page; JS will poll
            return render_template('waiting.html',
                                   user=session['user'],
                                   ride=new_ride,
                                   algo_trace=algo_trace)

    return render_template('ride.html', user=session['user'])


# ── Result page (direct link — both users can open) ──────────────

@app.route('/result/<ride_id>')
def result_page(ride_id):
    """Both the giver and requester can open /result/<their_ride_id>."""
    if 'user' not in session:
        return redirect(url_for('login'))
    data    = load_data()
    my_ride = next((r for r in data['rides'] if r['id'] == ride_id), None)
    if not my_ride or my_ride['user_id'] != session['user']['id']:
        return redirect(url_for('dashboard'))
    partner = next((r for r in data['rides']
                    if r['id'] == my_ride.get('matched_with')), None)
    trace   = data['algo_traces'].get(ride_id, {})
    return render_template('result.html',
                           user=session['user'],
                           ride=my_ride, match=partner,
                           algo_trace=trace,
                           success=(my_ride['status'] == 'matched' and partner is not None))


# ── APIs ─────────────────────────────────────────────────────────

@app.route('/api/areas')
def api_areas():
    from areas import AREAS
    return jsonify(list(AREAS.keys()))


@app.route('/api/fare')
def api_fare():
    from areas import calculate_fare
    fare = calculate_fare(request.args.get('pickup',''),
                          request.args.get('dropoff',''),
                          request.args.get('vehicle','car'))
    return jsonify({'fare': fare})


@app.route('/cancel/<ride_id>')
def cancel_ride(ride_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data()
    for r in data['rides']:
        if r['id'] == ride_id and r['user_id'] == session['user']['id']:
            r['status'] = 'cancelled'
            if r.get('matched_with'):
                for r2 in data['rides']:
                    if r2['id'] == r['matched_with']:
                        r2['status']       = 'searching'
                        r2['matched_with'] = None
    save_data(data)
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
