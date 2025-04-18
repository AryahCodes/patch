# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, emit
import firebase_admin
from firebase_admin import credentials, auth, firestore

cred = credentials.Certificate('firebase_key.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

issues = [
    {
        'id': 1,
        'title': 'Mold on ceiling',
        'description': 'Been here for 2 weeks',
        'tenant': 'tenant1',
        'landlord': 'landlord1',
        'status': 'Pending'
    },
    {
        'id': 2,
        'title': 'Water leak in kitchen',
        'description': 'Leak under sink',
        'tenant': 'tenant2',
        'landlord': 'landlord1',
        'status': 'Pending'
    },
    # Add more issues here for testing
]

# App routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        try:
            user = auth.create_user(email=email, password=password)

            db.collection('users').document(user.uid).set({
                'email': email,
                'role': role,
            })

            return redirect(url_for('login'))

        except Exception as e:
            return f"Error creating user: {e}"

    return render_template('signup.html')


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        role = request.form['role']

        # Get user by email
        try:
            user = auth.get_user_by_email(email)
            user_data = db.collection('users').document(user.uid).get().to_dict()

            if user_data['role'] != role:
                return "Incorrect role selected"

            session['username'] = email
            session['role'] = role

            if role == 'tenant':
                return redirect(url_for('tenant_dashboard'))
            else:
                return redirect(url_for('landlord_dashboard'))

        except Exception as e:
            return f"Login failed: {e}"

    return render_template('login.html')

@app.route('/tenant/dashboard')
def tenant_dashboard():
    if 'username' not in session or session.get('role') != 'tenant':
        return redirect(url_for('login'))

    user_issues = [issue for issue in issues if issue['tenant'] == session['username']]
    return render_template('tenant_dashboard.html', issues=user_issues)


@app.route('/landlord/dashboard')
def landlord_dashboard():
    if 'username' not in session or session.get('role') != 'landlord':
        return redirect(url_for('login'))

    user_issues = [issue for issue in issues if issue['landlord'] == session['username']]
    return render_template('landlord_dashboard.html', issues=user_issues)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route


@socketio.on('join')
def on_join(data):
    room = data.get('room')
    join_room(room)
    username = data.get('username')
    # Notify others in the room that a new user has joined
    emit('message', {'username': 'System', 'msg': f'{username} has joined the chat.'}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data.get('room')
    # Broadcast the received message to all users in the room
    emit('message', data, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
