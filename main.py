from flask import Flask, render_template, request, redirect, session, send_file
from functools import wraps
from hashlib import sha1
from secrets import compare_digest, token_bytes
from werkzeug.utils import secure_filename
from os import mkdir, path
from time import strftime, localtime, time
from mariadbcm import UseDB
from random import randint

app = Flask(__name__)
app.secret_key = "HackathonLeSsgoOoOoOoOoo"

# users = {"Aryan":(b'\x0c4\xb3\xb0U\xedT@\xad\x0e\x97L\xa3\x96\x99f', '2519fc6c8017ffef6b6b50a9ac3c85897809c63a'),}
# filesdb = {"Aryan": [['z3r0c1ph3r.pdf', 1655468236.725278]]}
datadb = {"Aryan": [[1655468236, 91, 37.1, 99, 102], [1655460000, 89, 37.5, 98, 108]]}
devicedb = {1:""}
pendingids = []
profiles = {}

# conf = {"user":"dynamichealth",
#     "password":"DynHelabcd1234",
#     "host":"dynamichealth.mysql.pythonanywhere-services.com",
#     "database":"dynamichealth$DHdb"}

conf = {"user":"DynamicH",
    "password":"DynHelabcd1234",
    "host":"localhost",
    "database":"DHdb"}


def check_login_status():
    def real_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "status" in session and "username" in session and session["status"] == "patient":
                return func(*args, **kwargs)
            return redirect("login")
        return wrapper
    return real_decorator


@app.route("/")
@check_login_status()
def index():
    if "status" not in session:
        session["status"] = "lo"
        session.permanent = True
    return redirect("home")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "status" not in session or session["status"] == "lo":
            session.permanent = True
            return render_template("login.html")
        else:
            return redirect("/home")

    uname = request.form["uname"]
    pword = request.form["pword"]

    with UseDB(conf) as cur:
        cur.execute("select username,iv,passhash from users where username = (%s)", (uname,))
        userd = cur.fetchone()
    if not userd: return render_template("login.html", errr="Username not found")
    salt, hash = userd[1], userd[2]
    if compare_digest(hash, sha1(salt+pword.encode()).hexdigest()):
        session["status"] = "patient"
        session["username"] = uname
        return redirect("/home")
    return render_template("login.html", errr="Incorrect Password")

@app.route("/logout")
def logout():
    if "status" in session:
        session["status"] = "lo"
    return redirect("login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if "status" not in session or session["status"] == "lo":
            session.permanent = True
            return render_template("register.html")
        else:
            return redirect("home")

    uname = request.form["uname"].strip()
    pword = request.form["pword"]
    with UseDB(conf) as cur:
        cur.execute("select username from users where username = (%s)", (uname,))
        usert = cur.fetchone()
    if usert: return render_template("register.html", errr="Username already taken")
    salt = token_bytes(16)

    with UseDB(conf) as cur:
        cur.execute("insert into users (username,iv,passhash) values (%s,%s,%s)", (uname, salt, sha1(salt+pword.encode()).hexdigest()))
    if not path.exists(f"uploads/{uname}"): mkdir(f"uploads/{uname}")
    return redirect("/")

@app.route("/data")
@check_login_status()
def data():
    with UseDB(conf) as cur:
        cur.execute("select filename,ts from files where username = (%s) ORDER BY ts desc", (session["username"],))
        filesl = cur.fetchall()
    f = [(fn,ts.strftime("%H:%M:%S %d-%m-%Y")) for fn,ts in filesl]

    d = [(strftime("%H:%M:%S %d-%m-%Y", localtime(j)), d1,d2,d3,d4) for j,d1,d2,d3,d4 in datadb["Aryan"]] if session["username"] not in datadb else [(strftime("%H:%M:%S %d-%m-%Y", localtime(j)), d1,d2,d3,d4) for j,d1,d2,d3,d4 in datadb[session["username"]]]

    return render_template("data.html", files=f, datas=d, histactc = "active", uname=session["username"])

@app.route("/home")
@check_login_status()
def home():
    return render_template("Home.html", homeactc = "active", uname=session["username"])

@app.route("/profile")
@check_login_status()
def profile():
    datas = {"s1":"","s2":"","s3":"","s4":"","s5":"","s6":"","s7":"","s8":"","s9":"","s10":""} if session["username"] not in profiles else profiles[session["username"]]
    return render_template("profile.html", profactc = "active", uname=session["username"], datas=datas)

@app.route("/profile/edit", methods=["GET", "POST"])
@check_login_status()
def profileedit():
    if request.method == "GET":
        datas = {"s1":"","s2":"","s3":"","s4":"","s5":"","s6":"","s7":"","s8":"","s9":"","s10":""} if session["username"] not in profiles else profiles[session["username"]]
        return render_template("profile.html", profactc = "active", uname=session["username"], datas=datas, editm=True)

    profiles[session["username"]] = request.form
    return redirect("/profile")


@app.route("/upload", methods = ["GET", "POST"])
@check_login_status()
def upload():
    if request.method == "GET":
        return """<html>
                   <body>
                      <form action = "/upload" method = "POST"
                         enctype = "multipart/form-data">
                         <input type = "file" name = "file" />
                         <input type = "submit"/>
                      </form>
                   </body>
                </html>"""

    f = request.files['file']
    fn = secure_filename(f.filename)
    f.save(f"uploads/{session['username']}/{fn}")

    with UseDB(conf) as cur:
        cur.execute("insert into files (username,filename) values (%s,%s)", (session['username'], fn))
    return redirect("data")

@app.route("/files")
@check_login_status()
def files():
    fname = request.args.get('fname')
    return send_file(f"../uploads/{session['username']}/{fname}")


@app.route("/getid")
def getid():
    i = 1
    while i in devicedb or i in pendingids:
        i = randint(100000,999999)
    pendingids.append(i)
    return str(i)

@app.route("/regdev", methods = ["GET", "POST"])
@check_login_status()
def regdev():
    if request.method == "GET":
        return """<html>
                   <body>
                      <form method = "POST">
                         <input type = "number" name = "key" >
                         <input type = "submit">
                      </form>
                   </body>
                </html>"""

    key = int(request.form["key"])
    if key in pendingids:
        pendingids.remove(key)
        devicedb[key] = session["username"]
        return "Registered Successfully"
    return "ID not found"

@app.route("/subdata")
def subdata():
    id = int(request.args.get('id'))
    d1 = request.args.get('d1')
    d2 = request.args.get('d2')
    d3 = request.args.get('d3')
    d4 = request.args.get('d4')
    t = time()
    datadb[devicedb[id]].append([t,d1,d2,d3,d4])
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0" ,port=8000 ,debug=True)
