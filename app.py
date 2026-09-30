from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os, json, datetime, secrets
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pathlib import Path
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'UPLOADS'
DATA_FILE = BASE_DIR / 'data.json'
USERS_FILE = BASE_DIR / 'users.json'
UPLOAD_FOLDER.mkdir(exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password, role='user'):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

def load_data():
    if not DATA_FILE.exists():
        save_data([])
    with open(DATA_FILE, encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_users():
    if not os.path.exists(USERS_FILE):
        save_users([])
        return []
    with open(USERS_FILE, encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

# Load users from file
users_data = load_users()
users = [User(u['id'], u['username'], u['password'], u['role']) for u in users_data]

@login_manager.user_loader
def load_user(user_id):
    for user in users:
        if user.id == int(user_id):
            return user
    return None


def find_file(unique_id):
    data = load_data()
    for file in data:
        if file.get('id') == unique_id:
            return file
    return None


def is_expired(file):
    try:
        expiry = datetime.datetime.fromisoformat(file['expiry_time'])
    except Exception:
        return False
    return datetime.datetime.now() > expiry


def preview_type(filename):
    extension = os.path.splitext(filename)[1].lower()
    if extension in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
        return 'image'
    if extension in {'.mp4', '.webm', '.ogg'}:
        return 'video'
    if extension in {'.mp3', '.wav', '.m4a', '.oga'}:
        return 'audio'
    if extension == '.pdf':
        return 'pdf'
    if extension in {'.txt', '.py', '.json', '.csv', '.md'}:
        return 'text'
    return None


@app.route('/')
@login_required
def home():
    data = load_data()
    user_files = [f for f in data if f.get('user_id') == current_user.id]
    return render_template('index.html', files=user_files)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        expiry = int(request.form['expiry'])

        filename = secure_filename(file.filename or '')
        if not filename:
            flash('Please choose a valid file')
            return redirect(url_for('upload'))
        unique_id = secrets.token_urlsafe(12)
        filepath = UPLOAD_FOLDER / filename
        file.save(filepath)

        expiry_date = datetime.datetime.now() + datetime.timedelta(hours=expiry)
        share_link = url_for('share', unique_id=unique_id, _external=True)

        data = load_data()
        data.append({
            "id": unique_id,
            "user_id": current_user.id,
            "filename": filename,
            "upload_time": str(datetime.datetime.now()),
            "expiry_time": str(expiry_date),
            "share_link": share_link
        })
        save_data(data)

        return redirect('/')

    return render_template('upload.html')

@app.route('/share/<unique_id>')
def share(unique_id):
    file = find_file(unique_id)
    if not file:
        return "File not found", 404

    if is_expired(file):
        return "This share link has expired.", 410

    return render_template('share.html', file=file, preview_type=preview_type(file['filename']))


@app.route('/preview/<unique_id>')
def preview(unique_id):
    file = find_file(unique_id)
    if not file:
        return "File not found", 404

    if is_expired(file):
        return "This file has expired and cannot be previewed.", 410

    return send_from_directory(str(UPLOAD_FOLDER), file['filename'])


@app.route('/download/<unique_id>')
def download(unique_id):
    file = find_file(unique_id)
    if not file:
        return "File not found", 404

    if is_expired(file):
        return "This file has expired and cannot be downloaded.", 410

    return send_from_directory(str(UPLOAD_FOLDER), file['filename'], as_attachment=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = next((u for u in users if u.username == username), None)
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('report'))
            else:
                return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('login.html')


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = next((u for u in users if u.username == username), None)
        if user and check_password_hash(user.password, password):
            if user.role == 'admin':
                login_user(user)
                return redirect(url_for('report'))
            else:
                flash('Access denied. Admin privileges required.')
                return redirect(url_for('admin_login'))
        flash('Invalid username or password')
    return render_template('admin_login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('signup'))
        
        users_data = load_users()
        if any(u['username'] == username for u in users_data):
            flash('Username already exists')
            return redirect(url_for('signup'))
        
        new_id = max(u['id'] for u in users_data) + 1 if users_data else 1
        hashed_password = generate_password_hash(password)
        new_user = {
            "id": new_id,
            "username": username,
            "password": hashed_password,
            "role": "user"
        }
        users_data.append(new_user)
        save_users(users_data)
        
        # Update global users list
        global users
        users = [User(u['id'], u['username'], u['password'], u['role']) for u in users_data]
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/files')
@login_required
def files():
    data = load_data()
    user_files = [f for f in data if f.get('user_id') == current_user.id]
    return render_template('files.html', files=user_files)

@app.route('/delete/<unique_id>', methods=['POST'])
@login_required
def delete_file(unique_id):
    data = load_data()
    file = find_file(unique_id)
    if file and file.get('user_id') is not None and file.get('user_id') != current_user.id and current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('files'))
    data = [f for f in data if f['id'] != unique_id]
    save_data(data)
    # Optionally delete the actual file
    if file:
        filepath = UPLOAD_FOLDER / file['filename']
        if os.path.exists(filepath):
            os.remove(filepath)
    flash('File deleted')
    return redirect(url_for('files'))
@app.route('/report')
@login_required
@admin_required
def report():
    data = load_data()
    usernames = {user.id: user.username for user in users}
    files_with_owners = [
        {**file, 'owner': usernames.get(file.get('user_id'), 'Unknown user')}
        for file in data
    ]
    return render_template('report.html', files=files_with_owners)

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
