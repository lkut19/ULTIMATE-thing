import datetime
import math
import time
from flask import Flask, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app= Flask(__name__)
with open(".gitignore","r") as url:
    dburl=url.read()

app.config["SQLALCHEMY_DATABASE_URI"] = dburl
app.secret_key = "keykeykeykeykeysecret!"
db= SQLAlchemy(app)

#home page
@app.route("/")
def index():
    username=session.get("username", None)
    if username:
        return render_template("home.html", logged_in=True, username=username)
    return render_template("home.html")

#login
@app.route("/login", methods=["GET","POST"])
def login():
    username=request.form.get("username", "")
    password=request.form.get("password", "")
    if username and password:
        user = passwords.query.filter_by(username=username).first()
        if user and user.password == hash(password):
            session["UID"] = user.id
            session["username"] = user.username
            return render_template("login.html", logged_in=True, username= username)
        else:
            return render_template("login.html", didnt_work=True, text="wrong username or password")
    return render_template("login.html")
    


#password db
class passwords(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String)
    password=db.Column(db.String)

#hash
def hash(password):
    hashed=[]
    for i,e in enumerate(password):
        temp= str(ord(e)+((i+1)*(i+4)))
        hashed.append(temp)
    return "".join(hashed)

#register
@app.route("/register", methods=["GET","POST"])
def register():
    username=request.form.get("username", "")
    password=request.form.get("password", "")
    if username and password:
        if passwords.query.filter_by(username=username).first():
            return "Username already exists"
        elif len(password)<8:
            return "Password must be at least 8 letters long"
        else:
            newuser= passwords(username=username, password=hash(password))
            db.session.add(newuser)
            db.session.commit()
            session["UID"] = newuser.id
            session["username"] = newuser.username
            return redirect(url_for("subjects"))
    return render_template("register.html", username=username, password=password)

#linker db
class linker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    UID=db.Column(db.Integer)
    SID=db.Column(db.String)
    __table_args__ = (db.UniqueConstraint('UID', 'SID', name='unique_user_subject'),)

class grades(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    UID=db.Column(db.Integer)
    SID=db.Column(db.String)
    targetgrade=db.Column(db.String)
    grade=db.Column(db.String)

@app.route("/subjects", methods=["GET","POST"])
def subjects():
    sublist=[]
    import subjects 
    import gradevalues
    gradelist=gradevalues.grades
    for subject in subjects.subjects:
        sublist.append(subject)

    if request.method == "POST":
        selected = request.form.getlist("subject")
        grade = request.form.getlist("grade")
        for thing in selected:
            if thing not in [link.SID for link in linker.query.filter_by(UID=session["UID"]).all()]:
                db.session.add(linker(UID=session["UID"], SID=thing))
            else:
                name=subjects.subjects[int(thing)-1]["name"]
                return f"Subject {name} is already registered."
        for position,letter in enumerate(grade):
            db.session.add(grades(UID=session["UID"],SID=selected[position], targetgrade=letter, grade="0"))

        db.session.commit()
        return "Subjects registered successfully"

    return render_template("subjects.html", sublist=sublist,gradelist=gradelist)

class sessions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    UID=db.Column(db.Integer)
    SID=db.Column(db.String)
    times=db.Column(db.String)
    UTX=db.Column(db.Integer)

@app.route("/timer", methods=["GET","POST"])
def timer():
    sublist=[]
    import subjects
    for subject in subjects.subjects:
        sublist.append(subject)

    if session.get("UID"):
        if request.method == "POST":
            selected = request.form.get("subject")
            seconds = request.form.get("seconds")
            UTX = int(time.time())
            if seconds == "":
                pass
            else:
                db.session.add(sessions(UID=session["UID"], SID=selected, times=seconds, UTX=int(UTX)))
                db.session.commit()
        return render_template("timer.html", sublist=sublist)
    else:
        return redirect(url_for("login"))


@app.route("/stats" ,methods=["GET","POST"])
def stats():
    import time
    import subjects as dictsubjects
    import gradevalues as dictgrades
    data=[]
    totaltime=0
    numsessions=0
    for s in sessions.query.all():
        if s.UID == session["UID"]: 
            subject=dictsubjects.subjects[int(s.SID)-1]["name"]
            times=int(s.times)

            found = False
            for item in data:
                if item["name"] == subject:
                    item["times"] += times   
                    found = True

            if not found:
                data.append({"SID": s.SID,"name": subject,"times": times,"weekavg": 0,"grade": ""
})
    
    for s in sessions.query.all():
        if s.UID == session["UID"]:
            totaltime+= int(s.times)
            numsessions+=1
    
    avgsessiontime=totaltime/numsessions

    if avgsessiontime >= 7200:
        style = "extravagant reviser"
    elif avgsessiontime >= 3600:
        style = "slow"
    elif avgsessiontime >= 1800:
        style = "medium"
    else:
        style = "fast"

    found = False
    for s in sessions.query.all():
        if s.UID == session["UID"]:
            timedifference = time.time() - int(s.UTX)
            weekspassed = math.ceil(timedifference / 604800)
            found = True
            break
    
    for item in data:
        item["weekavg"] = item["times"] / weekspassed
        item["times"] = format(item["times"])
        if item["weekavg"] >= (13 + dictsubjects.subjects[int(item["SID"])-1]["difficulty"]) * 3600:
            grade = 6
        elif item["weekavg"] >= (10 + dictsubjects.subjects[int(item["SID"])-1]["difficulty"]) * 3600:
            grade = 5
        elif item["weekavg"] >= (7 + dictsubjects.subjects[int(item["SID"])-1]["difficulty"]) * 3600:
            grade = 4
        elif item["weekavg"] >= (4 + dictsubjects.subjects[int(item["SID"])-1]["difficulty"]) * 3600:
            grade = 3
        elif item["weekavg"] >= (2 + dictsubjects.subjects[int(item["SID"])-1]["difficulty"]) * 3600:
            grade = 2
        elif item["weekavg"] >= (1 + dictsubjects.subjects[int(item["SID"])-1]["difficulty"]) * 3600:
            grade = 1
        else:
            grade = 0
        item["grade"] = grade
    
    paperdata=[]
    for paper in pastpapers.query.all():
        if paper.UID == session["UID"]:

            subject = dictsubjects.subjects[int(paper.SID)-1]["name"]

            paperdate = datetime.datetime.strptime(paper.date, "%Y-%m-%d")
            today = datetime.datetime.now()
            difference = today - paperdate
            weekssince = math.ceil(difference.days / 7)

            weight = math.exp(-weekssince * 0.12)
            value = int(paper.grade)
            print(f"Paper: {paper.SID}, Grade: {value}, Date: {paper.date}, Weeks Since: {weekssince}, Weight: {weight}")
            found = False
            for item in paperdata:
                if item["name"] == subject:
                    item["weightedgrade"] += value * weight
                    item["weighttotal"] += weight
                    found = True
                    break

            if not found:
                paperdata.append({"SID": paper.SID,"name": subject,"weightedgrade": (value * weight),"weighttotal": weight,"weightedavg": 0})
    
    for item in paperdata:
        item["weightedavg"]= math.floor(item["weightedgrade"] / item["weighttotal"])

    influence = 0.5

    for item in data:
        print(item)
        for paper in paperdata:
            if item["SID"] == paper["SID"]:
                value = item["grade"] * (1 - influence) + paper["weightedavg"] * influence
                item["grade"] = round(value)
                break 
        grades.query.filter_by(
            UID=session["UID"],
            SID=item["SID"]
        ).update({"grade": str(item["grade"])})

    db.session.commit()

    for item in data:
        print(f"Subject: {item['name']}, Grade: {item['grade']}")
        for g in dictgrades.grades:
            if g["val"] == item["grade"]:
                item["grade"] = g["grade"]

    return render_template("stats.html", data=data, style=style, paperdata=paperdata)

class pastpapers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    UID=db.Column(db.Integer)
    SID=db.Column(db.String)
    grade=db.Column(db.String)
    date=db.Column(db.String)

@app.route("/addpaper", methods=["GET","POST"])
def addpaper():
    from datetime import date
    sublist=[]
    import subjects 
    import gradevalues
    gradelist=gradevalues.grades
    for subject in subjects.subjects:
        sublist.append(subject)
    maxdate=date.today().isoformat()

    if request.method == "POST":
        selected = request.form.get("subject")
        grade = request.form.get("grade")
        date = request.form.get("date")

        db.session.add(pastpapers(UID=session["UID"], SID=selected, grade=grade, date=date))
        db.session.commit()

    return render_template("addpaper.html", sublist=sublist, gradelist=gradelist, maxdate=maxdate)

@app.route("/nextsession")
def nextsession():

    for item in grades.query.filter_by(UID=session["UID"]).all():
        if item.UID == session["UID"]:
            grade = int(item.grade)
            itemSID=int(item.SID)
            calculatetime(grade,itemSID)
    return render_template("nextsession.html")

def calculatetime(grade,itemsid):
    print(f"Calculating time for grade {grade} and subject ID {itemsid}")
    import subjects as dictsubjects
    if grade == 6:
        hours = (13 + dictsubjects.subjects[itemsid-1]["difficulty"]) * 3600
    elif grade == 5:
        hours = (10 + dictsubjects.subjects[itemsid-1]["difficulty"]) * 3600
    elif grade == 4:
        hours = (7 + dictsubjects.subjects[itemsid-1]["difficulty"]) * 3600
    elif grade == 3:
        hours = (4 + dictsubjects.subjects[itemsid-1]["difficulty"]) * 3600
    elif grade == 2:
        hours = (2 + dictsubjects.subjects[itemsid-1]["difficulty"]) * 3600
    elif grade == 1:
        hours = (1 + dictsubjects.subjects[itemsid-1]["difficulty"]) * 3600
    else:
        hours = 0
    return hours


def format(seconds):
    hour = seconds // 3600
    minute = (seconds % 3600) // 60
    second = seconds % 60
    return f"{hour}h {minute}m {second}s"

#database
with app.app_context():
    db.create_all()