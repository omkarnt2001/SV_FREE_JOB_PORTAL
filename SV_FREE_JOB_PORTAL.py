from flask import Flask, request, redirect, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2, os
from datetime import datetime
import urllib.parse
import smtplib
from email.mime.text import MIMEText
import random
from flask import send_from_directory
from twilio.rest import Client
import hashlib

otp_store = {}



app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecret123")

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER



# ---------------- EMAIL FUNCTION ----------------
def send_email(to_email, subject, message):
    try:
        sender = "yourrealemail@gmail.com"
        password = "16_digit_app_password"

        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Email error:", e)


# ---------------- SMS FUNCTION ----------------
def send_sms(to, message):
    client = Client("YOUR_SID", "YOUR_TOKEN")

    client.messages.create(
        body=message,
        from_="+1234567890",
        to=to
    )


# ---------------- GENERATE OTP ----------------
def generate_otp():
    return str(random.randint(100000, 999999))

def hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()




# ---------------- DATABASE ----------------
def get_db():
    try:
        db_url = os.environ.get("DATABASE_URL")

        if not db_url:
            raise Exception("❌ DATABASE_URL not set. Set it in environment variables.")

        return psycopg2.connect(db_url, sslmode='require')

    except Exception as e:
        print("DB ERROR:", e)
        raise e


def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()

        # ✅ USERS TABLE
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
        ''')

        # ✅ OTP TABLE
        cur.execute('''
        CREATE TABLE IF NOT EXISTS otp_verification (
            id SERIAL PRIMARY KEY,
            email TEXT,
            otp_hash TEXT,
            created_at TIMESTAMP,
            attempts INTEGER DEFAULT 0
        )
        ''')

        # ✅ JOBS TABLE
        cur.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            salary TEXT,
            hr_name TEXT,
            hr_contact TEXT,
            description TEXT
        )
        ''')

        # ✅ APPLICATIONS TABLE
        cur.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            user_email TEXT,
            job_id INTEGER,
            resume TEXT,
            status TEXT,
            date TEXT
        )
        ''')

        conn.commit()
        conn.close()

        print("✅ Database initialized successfully")

    except Exception as e:
        print("❌ DB INIT ERROR:", e)

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
        <a href="/otp_login" class="btn btn-warning w-100">📱 Login with OTP</a>

        <br>
        <a href="/signup">Create new account</a>
    </div>

    </body>
    </html>
    '''




# ---------------- OTP LOGIN ----------------
@app.route('/otp_login', methods=['GET','POST'])
def otp_login():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if not user:
            return "❌ Email not registered"

        otp = generate_otp()
        otp_hash = hash_otp(otp)

        # delete old OTP
        cur.execute("DELETE FROM otp_verification WHERE email=%s", (email,))

        # insert new OTP
        cur.execute("""
            INSERT INTO otp_verification (email, otp_hash, created_at)
            VALUES (%s, %s, %s)
        """, (email, otp_hash, datetime.now()))

        conn.commit()
        conn.close()

        send_email(email, "Your OTP", f"OTP: {otp}")
        send_sms("+91XXXXXXXXXX", f"Your OTP is {otp}")

        session['otp_email'] = email

        return redirect('/verify_otp')


    # ✅ UI SAME ठेव (NO CHANGE)
    return """
    <html>
    <head>
    <title>OTP Login</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
    body {
        background: linear-gradient(135deg,#141e30,#243b55);
        height:100vh;
        display:flex;
        justify-content:center;
        align-items:center;
        color:white;
    }

    .box {
        width:350px;
        background: rgba(255,255,255,0.1);
        padding:30px;
        border-radius:15px;
        backdrop-filter: blur(10px);
    }
    </style>
    </head>

    <body>

    <div class="box">
        <h4 class="text-center">📱 OTP Login</h4>

        <form method="POST">
            <input class="form-control mb-3" name="email" placeholder="Enter Email" required>
            <button class="btn btn-info w-100">Send OTP</button>
        </form>

        <br>
        <a href="/login" class="text-light">⬅ Back to Login</a>
    </div>

    </body>
    </html>
    """





# ---------------- VERIFY OTP ----------------
@app.route('/verify_otp', methods=['GET','POST'])
def verify_otp():

    email = session.get('otp_email')

    if not email:
        return redirect('/otp_login')

    if request.method == 'POST':
        user_otp = request.form['otp']

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT otp_hash, created_at, attempts 
            FROM otp_verification 
            WHERE email=%s
        """, (email,))

        data = cur.fetchone()

        if not data:
            return "❌ OTP not found"

        otp_hash, created_at, attempts = data

        if attempts >= 5:
            return "❌ Too many attempts"

        if (datetime.now() - created_at).total_seconds() > 300:
            return "❌ OTP expired"

        if hash_otp(user_otp) == otp_hash:
            session['user'] = email

            cur.execute("DELETE FROM otp_verification WHERE email=%s", (email,))
            conn.commit()
            conn.close()

            return redirect('/')
        else:
            cur.execute("""
                UPDATE otp_verification 
                SET attempts = attempts + 1 
                WHERE email=%s
            """, (email,))
            conn.commit()
            conn.close()

            return "❌ Wrong OTP"

   
    return """
    <html>
    <head>
    <title>Verify OTP</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
    body {
        background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
        height:100vh;
        display:flex;
        justify-content:center;
        align-items:center;
        color:white;
    }

    .box {
        width:350px;
        background: rgba(255,255,255,0.1);
        padding:30px;
        border-radius:15px;
        backdrop-filter: blur(10px);
    }
    </style>
    </head>

    <body>

    <div class="box">
        <h4 class="text-center">🔐 Enter OTP</h4>

        <form method="POST">
            <input class="form-control mb-3" name="otp" placeholder="Enter OTP" required>
            <button class="btn btn-success w-100">Verify</button>
        </form>

        <br>
        <a href="/resend_otp" class="btn btn-warning w-100">🔁 Resend OTP</a>
    </div>

    </body>
    </html>
    """


# ---------------- RESEND OTP ----------------
@app.route('/resend_otp')
def resend_otp():
    email = session.get('otp_email')

    if not email:
        return redirect('/otp_login')

    conn = get_db()
    cur = conn.cursor()

    otp = generate_otp()
    otp_hash = hash_otp(otp)

    # delete old OTP
    cur.execute("DELETE FROM otp_verification WHERE email=%s", (email,))

    # insert new OTP
    cur.execute("""
        INSERT INTO otp_verification (email, otp_hash, created_at)
        VALUES (%s, %s, %s)
    """, (email, otp_hash, datetime.now()))

    conn.commit()
    conn.close()

    send_email(email, "Resend OTP", f"Your OTP is: {otp}")

    return """
    <h3 style='text-align:center;'>✅ OTP Sent Again</h3>
    <div style='text-align:center;'>
        <a href='/verify_otp'>⬅ Back</a>
    </div>
    """







    



# ---------------- APPLY ----------------
@app.route('/apply/<int:id>', methods=['GET', 'POST'])
def apply(id):

    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        try:
            conn = get_db()
            cur = conn.cursor()

            file = request.files.get('resume')

            # ✅ FILE CHECK
            if not file or file.filename == '':
                return "<h3 style='color:red;text-align:center;'>❌ Please upload resume</h3>"

            # ✅ UNIQUE FILE NAME (NO ERROR EVER)
            filename = secure_filename(file.filename)
            unique_filename = str(datetime.now().timestamp()).replace(".", "") + "_" + filename

            # ❗ IMPORTANT: SAVE ONLY IF LOCAL (optional)
            try:
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                file.save(filepath)
            except:
                # 👉 cloud मध्ये save fail झाला तरी app crash होणार नाही
                unique_filename = "uploaded_" + unique_filename

            # ✅ MULTIPLE APPLY ALLOWED (NO CHECK)
            cur.execute("""
                INSERT INTO applications (user_email, job_id, resume, status, date)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                session['user'],
                id,
                unique_filename,
                'Pending',
                str(datetime.now())
            ))

            conn.commit()
            conn.close()

            # ✅ EMAIL SAFE
            try:
                send_email(
                    session['user'],
                    "Application Received - SV Job Portal",
                    "Hi 👋 Your application has been successfully submitted."
                )
            except:
                pass

            return """
            <html>
            <head>
                <title>Success</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body {
                        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
                        height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        color: white;
                    }
                    .box {
                        background: rgba(255,255,255,0.1);
                        padding: 40px;
                        border-radius: 20px;
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <div class="box">
                    <h1 style="color:lightgreen;">✅ Application Submitted</h1>
                    <p>You can apply multiple times 👍</p>

                    <a href="/" class="btn btn-light mt-3">🏠 Home</a>
                    <a href="/dashboard" class="btn btn-warning mt-3">📊 Dashboard</a>
                </div>
            </body>
            </html>
            """

        except Exception as e:
            return f"<h3 style='color:red;text-align:center;'>Error: {e}</h3>"

    # ---------------- GET UI ----------------
    return """
<html>
<head>
    <title>Apply Job</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
        body {
            margin:0;
            padding:0;
            height:100vh;
            display:flex;
            justify-content:center;
            align-items:center;
            background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
            font-family: 'Segoe UI', sans-serif;
            color:white;
        }

        .glass-card {
            width: 420px;
            padding: 35px;
            border-radius: 20px;
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(15px);
            box-shadow: 0 10px 40px rgba(0,0,0,0.4);
            animation: fadeIn 0.8s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity:0; transform:translateY(20px);}
            to { opacity:1; transform:translateY(0);}
        }

        .title {
            text-align:center;
            font-size:24px;
            font-weight:bold;
            margin-bottom:10px;
        }

        .subtitle {
            text-align:center;
            font-size:14px;
            color:#ccc;
            margin-bottom:20px;
        }

        .file-box {
            border:2px dashed rgba(255,255,255,0.4);
            padding:20px;
            text-align:center;
            border-radius:15px;
            cursor:pointer;
            transition:0.3s;
        }

        .file-box:hover {
            background: rgba(255,255,255,0.1);
        }

        input[type="file"] {
            display:none;
        }

        .btn-custom {
            margin-top:15px;
            border-radius:30px;
            padding:12px;
            font-weight:bold;
            letter-spacing:1px;
            transition:0.3s;
        }

        .btn-success:hover {
            transform: scale(1.05);
        }

        .back-btn {
            margin-top:10px;
            border-radius:30px;
        }

        .icon {
            font-size:40px;
            margin-bottom:10px;
        }
    </style>
</head>

<body>

    <div class="glass-card">

        <div class="title">🚀 Apply for Job</div>
        <div class="subtitle">Upload your resume & apply instantly</div>

        <form method="POST" enctype="multipart/form-data">

            <label class="file-box">
                <div class="icon">📄</div>
                <div>Select Resume</div>
                <small>PDF / DOC / DOCX</small>
                <input type="file" name="resume" required>
            </label>

            <button class="btn btn-success w-100 btn-custom">
                Submit Application
            </button>

        </form>

        <a href="/" class="btn btn-light w-100 back-btn">⬅ Back to Jobs</a>

    </div>

</body>
</html>
"""
# ---------------- USER DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT jobs.title, applications.status, applications.date
        FROM applications
        JOIN jobs ON jobs.id = applications.job_id
        WHERE applications.user_email=%s
    """, (session['user'],))

    data = cur.fetchall()
    conn.close()

    html = "<h2>User Dashboard</h2>"
    for d in data:
        html += f"<p>{d[0]} | {d[1]} | {d[2]}</p>"

    return html




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

        # ✅ CORRECT INDENTATION
        if user == os.environ.get("ADMIN_USER") and password == os.environ.get("ADMIN_PASS"):
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
        <a href="/admin/applications" class="btn btn-info mb-3">📄 View Applications</a>
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




# ---------------- ADMIN APPLICATIONS ----------------
@app.route('/admin/applications')
def admin_applications():
    if 'admin' not in session:
        return redirect('/admin_login')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT applications.id, applications.user_email, jobs.title, applications.resume, applications.status
        FROM applications
        JOIN jobs ON jobs.id = applications.job_id
        ORDER BY applications.id DESC
    """)

    data = cur.fetchall()
    conn.close()

    html = """
    <html>
    <head>
    <title>Applications</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
    body {
        background: #0f2027;
        color: white;
        padding:20px;
    }

    .card {
        border-radius: 12px;
        margin-bottom: 15px;
    }

    .status {
        font-weight: bold;
    }
    </style>
    </head>

    <body>

    <h2>📄 All Applications</h2>
    <a href="/admin" class="btn btn-light mb-3">⬅ Back</a>
    """

    for d in data:
        html += f"""
        <div class="card p-3 text-dark">
            <h5>👤 {d[1]}</h5>
            <p>💼 Job: {d[2]}</p>
            <p class="status">Status: {d[4]}</p>

            <a href="/download/{d[3]}" class="btn btn-primary btn-sm">⬇ Download Resume</a>
            <a href="/admin/update_status/{d[0]}/Approved" class="btn btn-success btn-sm">Approve</a>
            <a href="/admin/update_status/{d[0]}/Rejected" class="btn btn-danger btn-sm">Reject</a>
        </div>
        """

    html += "</body></html>"
    return html



# ---------------- DOWNLOAD RESUME ----------------
@app.route('/download/<filename>')
def download_file(filename):
    if 'admin' not in session:
        return "❌ Not allowed"

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)





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



# ---------------- UPDATE STATUS ----------------
@app.route('/admin/update_status/<int:id>/<status>')
def update_status(id, status):
    if 'admin' not in session:
        return redirect('/admin_login')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE applications SET status=%s WHERE id=%s", (status, id))

    conn.commit()
    conn.close()

    return redirect('/admin/applications')





# 👇 हे add कर
init_db()
