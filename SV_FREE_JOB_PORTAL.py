from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2, os
from datetime import datetime
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecret123")

# ---------------- DATABASE ----------------
def get_db():
    try:
        return psycopg2.connect(os.environ.get("DATABASE_URL"), sslmode='require')
    except Exception as e:
        print("DB ERROR:", e)
        raise e

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

    # ✅ Dynamic Login / Logout Button
    if 'user' in session:
        auth_btn = '<a href="/logout" class="btn btn-danger btn-sm">Logout</a>'
    else:
        auth_btn = '<a href="/login" class="btn btn-light btn-sm">Login</a>'

    html = f"""
    <html>
    <head>
        <title>SV Job Portal</title>

        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

        <style>
            body {{
                background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)),
                url('https://images.unsplash.com/photo-1521791136064-7986c2920216');
                background-size: cover;
                background-attachment: fixed;
                color: white;
            }}

            .navbar {{
                background: rgba(0,0,0,0.8);
            }}

            .job-card {{
                background: white;
                color: black;
                border-radius: 15px;
                padding: 15px;
                margin-bottom: 15px;
                transition: 0.3s;
                border-left: 5px solid #007bff;
            }}

            .job-card:hover {{
                transform: scale(1.05);
                box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            }}

            .btn-call {{ background: green; color:white; }}
            .btn-wa {{ background:#25D366; color:white; }}

            .hero {{
                text-align: center;
                padding: 60px 20px;
            }}

            .hero h1 {{
                font-size: 40px;
                font-weight: bold;
            }}
        </style>
    </head>

    <body>

    <!-- NAVBAR -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand d-flex align-items-center" href="#">
                <img width="40" src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png">
                SV Job Portal
            </a>

            <div>
                {auth_btn}
                <a href="/admin_login" class="btn btn-warning btn-sm">Admin</a>
            </div>
        </div>
    </nav>

    <!-- HERO -->
    <div class="hero">
        <h1>Find Your Dream Job 🚀</h1>
        <p>Apply instantly via Call or WhatsApp</p>
    </div>

    <div class="container">
    """

    # ✅ JOB LOOP
    for j in jobs:
        message = f"Hello {j[5]}, I am interested in {j[1]} job"
        whatsapp_url = f"https://wa.me/91{j[6]}?text={urllib.parse.quote(message)}"

        html += f"""
        <div class="job-card shadow">
            <h4>{j[1]}</h4>
            <p><b>{j[2]}</b> | 📍 {j[3]}</p>
            <p>💰 {j[4]}</p>
            <p>👤 {j[5]}</p>

            <div class="mb-2">
                <a class="btn btn-call btn-sm" href="tel:{j[6]}">📞 Call</a>
                <a class="btn btn-wa btn-sm" href="{whatsapp_url}" target="_blank">💬 WhatsApp</a>
                <a class="btn btn-primary btn-sm" href="/view/{j[0]}">👁 View</a>
                <a class="btn btn-success btn-sm" href="/apply/{j[0]}">Apply</a>
            </div>

            <hr>
            <p>{j[7]}</p>
        </div>
        """

    html += "</div></body></html>"
    return html
# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()

        # check user already exists
        cur.execute("SELECT * FROM users WHERE email=%s", (request.form['email'],))
        existing = cur.fetchone()

        if existing:
            return "⚠️ User already exists"

        # insert new user
        cur.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)", (
            request.form['name'],
            request.form['email'],
            generate_password_hash(request.form['password'])
        ))

        conn.commit()
        conn.close()

        return redirect('/login')

    return '''
    <html>
    <head>
    <title>Signup</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
    body {
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)),
        url('https://images.unsplash.com/photo-1521791136064-7986c2920216');
        background-size: cover;
        color: white;
    }

    .box {
        max-width:400px;
        margin:auto;
        margin-top:100px;
        background:white;
        color:black;
        padding:20px;
        border-radius:10px;
    }
    </style>
    </head>

    <body>

    <div class="box">
        <h3>Signup</h3>

        <form method="POST">
            <input class="form-control mb-2" name="name" placeholder="Name" required>
            <input class="form-control mb-2" name="email" placeholder="Email" required>
            <input class="form-control mb-2" name="password" type="password" placeholder="Password" required>

            <button class="btn btn-success w-100">Signup</button>
        </form>

        <br>
        <a href="/login">Already have account? Login</a>
    </div>

    </body>
    </html>
    '''

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()

        email = request.form['email']
        password = request.form['password']

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        conn.close()

        if user:
            if check_password_hash(user[3], password):
                session['user'] = user[2]
                return redirect('/')
            else:
                return "❌ Wrong Password"
        else:
            return "❌ User Not Found"

    return '''
    <html>
    <head>
    <title>Login</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
    body {
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)),
        url('https://images.unsplash.com/photo-1521791136064-7986c2920216');
        background-size: cover;
        color: white;
    }

    .box {
        max-width:400px;
        margin:auto;
        margin-top:100px;
        background:white;
        color:black;
        padding:20px;
        border-radius:10px;
    }
    </style>
    </head>

    <body>

    <div class="box">
        <h3>Login</h3>

        <form method="POST">
            <input class="form-control mb-2" name="email" placeholder="Email" required>
            <input class="form-control mb-2" name="password" type="password" placeholder="Password" required>

            <button class="btn btn-primary w-100">Login</button>
        </form>

        <br>
        <a href="/signup">Create new account</a>
    </div>

    </body>
    </html>
    '''



# ---------------- APPLY ----------------
@app.route('/apply/<int:id>')
def apply(id):
    if 'user' not in session:
        return redirect('/login')

    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO applications (user_email, job_id, resume, status, date)
        VALUES (%s, %s, %s, %s, %s)
        """, (
            session['user'],
            id,
            '',
            'Pending',
            str(datetime.now())
        ))

        conn.commit()
        conn.close()

        return "<h3 style='color:green'>✅ Applied Successfully</h3>"

    except Exception as e:
        return f"<h3 style='color:red'>Error: {e}</h3>"




# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
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


# ---------------- VIEW JOB ----------------
@app.route('/view/<int:id>')
def view_job(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM jobs WHERE id=%s", (id,))
    job = cur.fetchone()

    conn.close()

    if not job:
        return "Job Not Found"

    return f"""
    <html>
    <head>
    <title>{job[1]}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>

    <body class="bg-dark text-white">

    <div class="container mt-5">
        <div class="card p-4 text-dark">
            <h2>{job[1]}</h2>
            <p><b>Company:</b> {job[2]}</p>
            <p><b>Location:</b> {job[3]}</p>
            <p><b>Salary:</b> {job[4]}</p>
            <p><b>HR:</b> {job[5]}</p>
            <p><b>Contact:</b> {job[6]}</p>

            <hr>
            <p>{job[7]}</p>

            <a href="/" class="btn btn-secondary">⬅ Back</a>
            <a href="/apply/{job[0]}" class="btn btn-success">Apply Now</a>
        </div>
    </div>

    </body>
    </html>
    """

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

    html = """
    <html>
    <head>
    <title>Admin Panel</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
    body {
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)),
        url('https://i.imgur.com/8Km9tLL.png'); /* replace with your logo link */
        background-size: 300px;
        background-repeat: no-repeat;
        background-position: center;
        background-attachment: fixed;
        color: white;
    }

    .card {
        border-radius: 12px;
        margin-bottom: 10px;
    }

    .header {
        text-align:center;
        padding:20px;
        font-size:28px;
        font-weight:bold;
    }
    </style>
    </head>

    <body>

    <div class="header">⚙️ Admin Dashboard</div>

    <div class="container">
        <a href="/admin/post_job" class="btn btn-success mb-3">+ Post Job</a>
    """

    for j in jobs:
        html += f"""
        <div class="card p-3">
            <h5>{j[1]}</h5>
            <p>{j[2]}</p>
            <a href="/admin/delete/{j[0]}" class="btn btn-danger btn-sm">Delete</a>
        </div>
        """

    html += "</div></body></html>"
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
    <html>
    <head>
    <title>Post Job</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
    body {
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)),
        url('https://i.imgur.com/8Km9tLL.png');
        background-size: 300px;
        background-repeat: no-repeat;
        background-position: center;
        color: white;
    }

    .form-box {
        max-width:500px;
        margin:auto;
        margin-top:50px;
        background:white;
        padding:20px;
        border-radius:10px;
        color:black;
    }
    </style>
    </head>

    <body>

    <div class="form-box">
        <h3>Post Job</h3>

        <form method="POST">
            <input class="form-control mb-2" name="title" placeholder="Job Title">
            <input class="form-control mb-2" name="company" placeholder="Company">
            <input class="form-control mb-2" name="location" placeholder="Location">
            <input class="form-control mb-2" name="salary" placeholder="Salary">
            <input class="form-control mb-2" name="hr_name" placeholder="HR Name">
            <input class="form-control mb-2" name="hr_contact" placeholder="HR Contact">
            <textarea class="form-control mb-2" name="description" placeholder="Description"></textarea>

            <button class="btn btn-primary w-100">Post Job</button>
        </form>
    </div>

    </body>
    </html>
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
