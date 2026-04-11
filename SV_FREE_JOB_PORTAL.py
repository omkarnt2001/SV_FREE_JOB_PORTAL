from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2, os
from datetime import datetime
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecret123")

# ---------------- DATABASE ----------------
def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"), sslmode='require')

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT,
        password TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        salary TEXT,
        hr_name TEXT,
        hr_contact TEXT,
        description TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS applications (
        id SERIAL PRIMARY KEY,
        user_email TEXT,
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
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs")
    jobs = cur.fetchall()
    conn.close()

    html = "<h1>💼 SV Job Portal</h1><a href='/login'>Login</a> | <a href='/admin_login'>Admin</a><br><br>"

    for j in jobs:
        message = f"Hello {j[5]}, I am interested in {j[1]} job"
        whatsapp_url = f"https://wa.me/91{j[6]}?text={urllib.parse.quote(message)}"

        html += f"""
        <div>
        <h2>{j[1]}</h2>
        <p>{j[2]} | {j[3]}</p>
        <p>💰 {j[4]}</p>
        <p>👤 {j[5]}</p>
        <p>📞 <a href='tel:{j[6]}'>{j[6]}</a></p>
        <p>💬 <a href='{whatsapp_url}' target='_blank'>WhatsApp</a></p>
        <p>{j[7]}</p>
        <a href='/apply/{j[0]}'>Apply</a>
        </div><hr>
        """

    return html

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)", (
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
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (request.form['email'],))
        user = cur.fetchone()
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
@app.route('/apply/<int:id>')
def apply(id):
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO applications (user_email,job_id,status,date) VALUES (%s,%s,%s,%s)", (
        session['user'], id, 'Pending', str(datetime.now())
    ))
    conn.commit()
    conn.close()

    return "✅ Applied"

# ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form.get('user', '').strip().lower()
        password = request.form.get('pass', '').strip()

        if user == "admin" and password == "1234":
            session['admin'] = True
            return redirect('/admin')

        return "❌ Wrong Admin"

    return '''
    <form method="POST">
    <input name="user" placeholder="Username"><br>
    <input name="pass" placeholder="Password" type="password"><br>
    <button>Login</button>
    </form>
    '''

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect('/admin_login')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs")
    jobs = cur.fetchall()
    conn.close()

    html = "<h2>Admin</h2><a href='/admin/post_job'>Post Job</a><br><br>"

    for j in jobs:
        html += f"<p>{j[1]} - {j[2]} <a href='/admin/delete/{j[0]}'>Delete</a></p>"

    return html

# ---------------- POST JOB ----------------
@app.route('/admin/post_job', methods=['GET','POST'])
def post_job():
    if 'admin' not in session:
        return redirect('/admin_login')

    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO jobs (title,company,location,salary,hr_name,hr_contact,description)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
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
    <input name="hr_name" placeholder="HR Name"><br>
    <input name="hr_contact" placeholder="HR Contact Number"><br>
    <textarea name="description"></textarea><br>
    <button>Post</button>
    </form>
    '''

# ---------------- DELETE ----------------
@app.route('/admin/delete/<int:id>')
def delete_job(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM jobs WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# 👇 हे add कर
init_db()
