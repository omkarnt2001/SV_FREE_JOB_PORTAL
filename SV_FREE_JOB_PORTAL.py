from flask import Flask, request, redirect, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecret123")
app.config['UPLOAD_FOLDER'] = 'uploads'

# ---------------- EMAIL ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
mail = Mail(app)

# ---------------- ADMIN ----------------
ADMIN_USER = "admin"
ADMIN_PASS = "1234"

if not os.path.exists('uploads'):
    os.makedirs('uploads')

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('final.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        password TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        salary TEXT,
        hr_name TEXT,
        hr_contact TEXT,
        description TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY,
        user TEXT,
        job_id INTEGER,
        resume TEXT,
        status TEXT,
        date TEXT
    )''')

    conn.commit()
    conn.close()

# ---------------- HOME ----------------
@app.route('/')
def home():
    init_db()
    conn = sqlite3.connect('final.db')
    jobs = conn.execute("SELECT * FROM jobs").fetchall()
    conn.close()

    html = "<h1>💼 SV Job Portal</h1><a href='/login'>Login</a> | <a href='/admin_login'>Admin</a><br><br>"

    for j in jobs:
        html += f"""
        <div>
        <h2>{j[1]}</h2>
        <p>{j[2]} | {j[3]}</p>
        <p>💰 {j[4]}</p>
        <p>👤 {j[5]}</p>
        <p>📞 <a href='tel:{j[6]}'>Call</a></p>
        <p>{j[7]}</p>
        <a href='/apply/{j[0]}'>Apply</a>
        </div><hr>
        """

    return html

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        conn = sqlite3.connect('final.db')
        conn.execute("INSERT INTO users VALUES(NULL,?,?,?)", (
            request.form['name'],
            request.form['email'],
            generate_password_hash(request.form['password'])
        ))
        conn.commit()
        conn.close()
        return redirect('/login')

    return '''
    <form method="POST">
    <input name="name"><br>
    <input name="email"><br>
    <input name="password"><br>
    <button>Signup</button>
    </form>
    '''

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = sqlite3.connect('final.db')
        user = conn.execute("SELECT * FROM users WHERE email=?", (request.form['email'],)).fetchone()
        conn.close()

        if user and check_password_hash(user[3], request.form['password']):
            session['user'] = user[2]
            return redirect('/')

        return "❌ Invalid Login"

    return '''
    <form method="POST">
    <input name="email"><br>
    <input name="password"><br>
    <button>Login</button>
    </form>
    '''

# ---------------- APPLY ----------------
@app.route('/apply/<int:id>', methods=['GET','POST'])
def apply(id):
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        file = request.files['resume']
        filename = str(datetime.now().timestamp()) + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect('final.db')
        conn.execute("INSERT INTO applications VALUES(NULL,?,?,?,?,?)", (
            session['user'], id, filename, 'Pending', str(datetime.now())
        ))
        conn.commit()
        conn.close()

        return "✅ Applied"

    return '''
    <form method="POST" enctype="multipart/form-data">
    <input type="file" name="resume"><br>
    <button>Submit</button>
    </form>
    '''

# ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form['user'].strip().lower()
        password = request.form['pass'].strip()

        if user == ADMIN_USER.lower() and password == ADMIN_PASS:
            session['admin'] = True
            return redirect('/admin')

        return "❌ Wrong Admin"

    return '''
    <form method="POST">
    <input name="user"><br>
    <input name="pass"><br>
    <button>Login</button>
    </form>
    '''

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect('/admin_login')

    conn = sqlite3.connect('final.db')
    jobs = conn.execute("SELECT * FROM jobs").fetchall()
    conn.close()

    html = "<h2>Admin</h2><a href='/admin/post_job'>Post Job</a><br><br>"

    for j in jobs:
        html += f"""
        <p>{j[1]} - {j[2]}
        <a href='/admin/delete/{j[0]}'>Delete</a></p>
        """

    return html

# ---------------- POST JOB ----------------
@app.route('/admin/post_job', methods=['GET','POST'])
def post_job():
    if 'admin' not in session:
        return redirect('/admin_login')

    if request.method == 'POST':
        conn = sqlite3.connect('final.db')
        conn.execute("INSERT INTO jobs VALUES(NULL,?,?,?,?,?,?,?)", (
            request.form['title'],
            request.form['company'],
            request.form['location'],
            request.form['salary'],
            request.form['hr_name'],
            request.form['hr_contact'],
            request.form['description']
        ))
        conn.commit()
        conn.close()
        return redirect('/admin')

    return '''
    <form method="POST">
    <input name="title"><br>
    <input name="company"><br>
    <input name="location"><br>
    <input name="salary"><br>
    <input name="hr_name"><br>
    <input name="hr_contact"><br>
    <textarea name="description"></textarea><br>
    <button>Post</button>
    </form>
    '''

# ---------------- DELETE ----------------
@app.route('/admin/delete/<int:id>')
def delete_job(id):
    conn = sqlite3.connect('final.db')
    conn.execute("DELETE FROM jobs WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

