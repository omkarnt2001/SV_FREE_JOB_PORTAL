from flask import Flask, request, redirect, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from dotenv import load_dotenv
import sqlite3, os
from datetime import datetime

# ---------------- ENV ----------------
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY","mysecret123")
app.config['UPLOAD_FOLDER']='uploads'

# ---------------- EMAIL ----------------
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=587
app.config['MAIL_USE_TLS']=True
app.config['MAIL_USERNAME']=os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD']=os.environ.get("MAIL_PASSWORD")
mail=Mail(app)

# ---------------- ADMIN ----------------
ADMIN_USER="admin"
ADMIN_PASS="1234"

if not os.path.exists('uploads'):
    os.makedirs('uploads')

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('final.db')
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT
    )''')

    # Jobs table
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        salary TEXT,
        hr TEXT,
        description TEXT
    )''')

    # Applications table
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY, user TEXT, job_id INTEGER,
        resume TEXT, status TEXT, date TEXT
    )''')

    # Insert default jobs if empty
    c.execute("SELECT COUNT(*) FROM jobs")
    if c.fetchone()[0]==0:
        c.execute("INSERT INTO jobs VALUES (NULL,'Back Office','SV Associates','Thane','15k-20k','Ramesh','Handles back office tasks')")
        c.execute("INSERT INTO jobs VALUES (NULL,'Telecaller','SV Associates','Diva','12k-18k','Sita','Handles outbound calls')")

    conn.commit()
    conn.close()

# ---------------- HOME ----------------
@app.route('/')
def home():
    init_db()   # 🔥 इथे add करायचं आहे (FIRST LINE)

    loc=request.args.get('loc','')
    conn=sqlite3.connect('final.db')

    if loc:
        jobs=conn.execute("SELECT * FROM jobs WHERE location LIKE ?",('%'+loc+'%',)).fetchall()
    else:
        jobs=conn.execute("SELECT * FROM jobs").fetchall()

    conn.close()

    html='''<style>
    body{font-family:Arial;background:#f4f6f9;}
    .card{background:white;padding:15px;margin:10px;border-radius:10px;box-shadow:0 0 10px #ccc;}
    .top{text-align:center;}
    </style>
    <div class="top">
    <h1>💼 SV Associates Job Portal</h1>
    <a href="/login">Login</a> | 
    <a href="/signup">Signup</a> | 
    <a href="/admin_login">Admin Login</a>
    <br><br>
    <form>
    <select name="loc">
        <option value="">All Locations</option>
        <option>Thane</option>
        <option>Diva</option>
    </select>
    <button>Filter</button>
    </form>
    </div>
    '''
    for j in jobs:
        description = j[6] if len(j)>6 else "No Description"
        html += f"""
        <div class='card'>
        <h2>{j[1]}</h2>
        <p>{j[2]} | {j[3]}</p>
        <p>💰 {j[4]}</p>
        <p>📝 {description}</p>
        <p>📞 <a href='tel:{j[5]}'>Call</a> | 💬 <a href='https://wa.me/{j[5]}'>WhatsApp</a></p>
        <a href='/apply/{j[0]}'>Apply</a>
        </div>
        """
    return html

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email'].strip().lower()
        password=generate_password_hash(request.form['password'])
        conn=sqlite3.connect('final.db')
        conn.execute("INSERT INTO users VALUES(NULL,?,?,?)",(name,email,password))
        conn.commit()
        conn.close()
        return redirect('/login')
    return '''
    <h2>Signup</h2>
    <form method="POST">
    <input name="name" placeholder="Name"><br>
    <input name="email" placeholder="Email"><br>
    <input name="password" placeholder="Password"><br>
    <button>Signup</button>
    </form>
    '''

# ---------------- LOGIN ----------------
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email'].strip().lower()
        password=request.form['password']
        conn=sqlite3.connect('final.db')
        user=conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        conn.close()
        if user and check_password_hash(user[3],password):
            session['user']=email
            return redirect('/')
        return "❌ Invalid Login"
    return '''
    <h2>Login</h2>
    <form method="POST">
    <input name="email" placeholder="Email"><br>
    <input name="password" placeholder="Password"><br>
    <button>Login</button>
    </form>
    '''

# ---------------- APPLY ----------------
@app.route('/apply/<int:id>',methods=['GET','POST'])
def apply(id):
    if 'user' not in session:
        return redirect('/login')
    if request.method=='POST':
        file=request.files['resume']
        filename=str(datetime.now().timestamp())+"_"+file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        conn=sqlite3.connect('final.db')
        conn.execute("INSERT INTO applications VALUES(NULL,?,?,?,?,?)",(session['user'],id,filename,'Pending',str(datetime.now())))
        conn.commit()
        conn.close()
        try:
            msg=Message("New Application",sender=app.config['MAIL_USERNAME'],recipients=[app.config['MAIL_USERNAME']])
            msg.body=f"{session['user']} applied for job ID {id}"
            mail.send(msg)
        except:
            print("Email error")
        return "✅ Applied Successfully"
    return '''
    <h3>Upload Resume</h3>
    <form method="POST" enctype="multipart/form-data">
    <input type="file" name="resume"><br>
    <button>Submit</button>
    </form>
    '''

# ---------------- DOWNLOAD ----------------
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory('uploads', filename, as_attachment=True)

# ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        if request.form['user']==ADMIN_USER and request.form['pass']==ADMIN_PASS:
            session['admin']=True
            return redirect('/admin')
        return "❌ Wrong Admin"
    return '''
    <h2>Admin Login</h2>
    <form method="POST">
    <input name="user" placeholder="Username"><br>
    <input name="pass" placeholder="Password"><br>
    <button>Login</button>
    </form>
    '''

# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect('/admin_login')
    html='''<h2>Admin Dashboard</h2>
    <a href="/admin/post_job">➕ Post New Job</a><br><br>
    <h3>Jobs List</h3>
    <table border=1>
    <tr><th>Title</th><th>Company</th><th>Location</th><th>Salary</th><th>HR Name</th><th>Description</th><th>Action</th></tr>'''
    conn=sqlite3.connect('final.db')
    jobs=conn.execute("SELECT * FROM jobs").fetchall()
    for j in jobs:
        html+=f"""
        <tr>
        <td>{j[1]}</td>
        <td>{j[2]}</td>
        <td>{j[3]}</td>
        <td>{j[4]}</td>
        <td>{j[5]}</td>
        <td>{j[6]}</td>
        <td><a href='/admin/delete_job/{j[0]}'>Delete</a></td>
        </tr>
        """
    html+="</table><br><h3>Applications</h3><table border=1>"
    html+="<tr><th>User</th><th>Job ID</th><th>Resume</th><th>Status</th><th>Action</th></tr>"
    apps=conn.execute("SELECT * FROM applications").fetchall()
    conn.close()
    for a in apps:
        html+=f"""
        <tr>
        <td>{a[1]}</td>
        <td>{a[2]}</td>
        <td><a href='/download/{a[3]}'>Download</a></td>
        <td>{a[4]}</td>
        <td><a href='/status/{a[0]}/Selected'>Select</a> | <a href='/status/{a[0]}/Rejected'>Reject</a></td>
        </tr>
        """
    html+="</table>"
    return html

# ---------------- POST JOB ----------------
@app.route('/admin/post_job',methods=['GET','POST'])
def post_job():
    if 'admin' not in session:
        return redirect('/admin_login')
    if request.method=='POST':
        title=request.form['title']
        company=request.form['company']
        location=request.form['location']
        salary=request.form['salary']
        hr=request.form['hr']
        description=request.form['description']
        conn=sqlite3.connect('final.db')
        conn.execute("INSERT INTO jobs VALUES(NULL,?,?,?,?,?,?)",(title,company,location,salary,hr,description))
        conn.commit()
        conn.close()
        return redirect('/admin')
    return '''
    <h2>Post New Job</h2>
    <form method="POST">
    <input name="title" placeholder="Job Title"><br>
    <input name="company" placeholder="Company"><br>
    <input name="location" placeholder="Location"><br>
    <input name="salary" placeholder="Salary"><br>
    <input name="hr" placeholder="HR Name"><br>
    <textarea name="description" placeholder="Job Description"></textarea><br>
    <button>Post Job</button>
    </form>
    '''

# ---------------- DELETE JOB ----------------
@app.route('/admin/delete_job/<int:id>')
def delete_job(id):
    if 'admin' not in session:
        return redirect('/admin_login')
    conn=sqlite3.connect('final.db')
    conn.execute("DELETE FROM jobs WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# ---------------- APPLICATION STATUS ----------------
@app.route('/status/<int:id>/<status>')
def status(id,status):
    conn=sqlite3.connect('final.db')
    conn.execute("UPDATE applications SET status=? WHERE id=?",(status,id))
    conn.commit()
    conn.close()
    return redirect('/admin')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    init_db()
    app.run()
