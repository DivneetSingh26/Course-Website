# required imports
# the sqlite3 library allows us to communicate with the sqlite database
import sqlite3
# we are adding the import 'g' which will be used for the database
from flask import Flask, render_template, request, g, session, redirect
from flask import url_for, escape, flash

# the database file we are going to communicate with
DATABASE = './assignment3.db'

# connects to the database


# the function get_db is taken from here
# https://flask.palletsprojects.com/en/1.1.x/patterns/sqlite3/
def get_db():
    # if there is a database, use it
    db = getattr(g, '_database', None)
    if db is None:
        # otherwise, create a database to use
        db = g._database = sqlite3.connect(DATABASE)
    return db

# converts the tuples from get_db() into dictionaries
# (don't worry if you don't understand this code)


# the function make_dicts is taken from here
# https://flask.palletsprojects.com/en/1.1.x/patterns/sqlite3/
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# given a query, executes and returns the result
# (don't worry if you don't understand this code)


# the function query_db is taken from here
# https://flask.palletsprojects.com/en/1.1.x/patterns/sqlite3/
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# tells Flask that "this" is the current running app
app = Flask(__name__)
app.secret_key = b'cscb20'


# the function close_connection is taken from here
# https://flask.palletsprojects.com/en/1.1.x/patterns/sqlite3/
# this function gets called when the Flask app shuts down
# tears down the database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        # close the database if we are connected to it
        db.close()


@app.route('/')
def index():
    if 'email' in session:
        return redirect(url_for('home'))
    return redirect(url_for("login"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        sql = """
        SELECT *
        FROM User
        """
        results = query_db(sql, args=(), one=False)
        for result in results:
            if result[3] == request.form['email']:
                if result[4] == request.form['password']:
                    session['email'] = request.form['email']
                    session['type'] = result[5]
                    return redirect(url_for('index'))

        flash("Invalid Credentials", category="danger")
        return redirect(url_for("login"))

    elif 'email' in session:
        return redirect(url_for('index'))
    else:
        return render_template("login.html")


@app.route('/create-account', methods=['GET', 'POST'])
def createAccount():
    if request.method == 'POST':
        userName = request.form["email"]
        userNameConfirm = request.form["emailConfirm"]
        fName = request.form["first_name"]
        lName = request.form["last_name"]
        password = request.form["password"]
        passwordConfirm = request.form["passwordConfirm"]
        accountType = request.form["type"]
        if password == passwordConfirm and userName == userNameConfirm:
            try:
                sql = """
              INSERT INTO User (first_name,last_name,uname,password,type)
              VALUES (?,?,?,?,?)
              """

                data = [fName, lName, userName, password, accountType]
                db = get_db()
                res = db.execute(sql, data)
                db.commit()
                flash("Account Created", category='msg')
            except sqlite3.IntegrityError as UserNameExceptio:
                flash("This e-mail is already associated with an account! ",
                      category="danger")

        else:
            flash("Your passwords or emails do not match!", category="danger")

        return redirect(url_for("create"))

    elif 'email' in session:
        return redirect(url_for('index'))
    else:
        return render_template("login.html")


# route logout
@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))


# route create account page
@app.route("/create")
def create():
    return render_template("create.html")


# route home page
@app.route("/index")
def home():
    if 'email' in session:
        return render_template("index.html", accountInfo=session['email'])
    return redirect(url_for("login"))


# route course page
@app.route("/course")
def course():
    if 'email' in session:
        return render_template("course.html")
    return redirect(url_for("login"))


# route lectures page
@app.route("/lectures")
def lectures():
    if 'email' in session:
        return render_template("lectures.html")
    return redirect(url_for("login"))

# get account info


def getAccountInfo():
    # query account info
    sql = """
      SELECT first_name, last_name, uname, type FROM User WHERE uname = ?;
      """
    data = [session['email']]
    db = get_db()
    accountInfo = db.execute(sql, data)
    infoList = []

    for i in accountInfo:
        infoList.append(i)
    return infoList


# route lectures page
@app.route("/account")
def account():
    if 'email' in session:
        accountInfo = getAccountInfo()
        return render_template("account.html", accountInfo=accountInfo)
    return redirect(url_for("login"))


# route team page
@app.route("/team")
def team():
    if 'email' in session:
        return render_template("team.html")
    return redirect(url_for("login"))


# route labs page
@app.route("/labs")
def labs():
    if 'email' in session:
        return render_template("labs.html")
    return redirect(url_for("login"))


# get instructors
def getInst():
    # query to get inst
    db = get_db()
    sql = """
        SELECT * FROM User WHERE type='instructor';
        """
    res = db.execute(sql)
    inst = ()
    instList = []
    for i in res:
        inst = (i[1] + " " + i[2], i[3])
        instList.append(inst)
    return instList


# get inst feedback
def getInstFeedback():
    sql = """
        SELECT * FROM Anonfeedback WHERE uname = ?;
        """
    instUname = session['email']

    data = [instUname]
    res = get_db().execute(sql, data)
    feedbackList = []
    for i in res:
        feedbackList.append(i)
    return feedbackList


# route feedback page
@app.route("/feedback", methods=['GET', 'POST'])
def feedback():
    if 'email' in session:
        # get account info and check if account holder is student or not
        accountInfo = getAccountInfo()
        if accountInfo[0][3] == 'student':
            # load inst onto select
            instName = getInst()
            if request.method == 'POST':
                selectedInst = request.form["type"]
                improve = request.form["improve"]
                doesWell = request.form["does_well"]
                additionalComments = request.form["additional_comments"]
                sql = """
                INSERT INTO Anonfeedback (uname,improve,does_well,
                additional_comments) VALUES (?,?,?,?)
                """

                data = [selectedInst, improve, doesWell, additionalComments]
                db = get_db()
                res = db.execute(sql, data)
                db.commit()
                flash("Your feedback was submitted!", category="success")
            return render_template("studentFeedback.html", instName=instName)

        # account holder is inst show inst view
        elif accountInfo[0][3] == 'instructor':
            instFeedback = getInstFeedback()
            return render_template("instFeedback.html",
                                   instFeedback=instFeedback)
    return redirect(url_for('login'))


# route assignments page
@app.route("/assignments")
def assignments():
    if 'email' in session:
        return render_template("assignments.html")
    return redirect(url_for("login"))


# get student grades


def getStudentMarks():
    sql = """
        SELECT * FROM Marks WHERE uname = ?;
        """
    studentUname = session['email']

    data = [studentUname]
    res = get_db().execute(sql, data)
    marksList = []
    for i in res:
        marksList.append(i)
    return marksList

# get remark reqs


def getRemarkReq():
    sql = """
        SELECT * FROM Remark_Requests;
        """
    res = get_db().execute(sql)
    reqList = []
    for i in res:
        reqList.append(i)
    return reqList

# PARSE GRADE


def parseGrade(string):
    newS = string.split(", ")
    return newS

# get all student grades


def getAllMark():
    sql = """
        SELECT * FROM Marks;
        """

    res = get_db().execute(sql)
    marksList = []
    for i in res:
        marksList.append(i)
    return marksList


# route marks page
@app.route("/marks", methods=['GET', 'POST'])
def marks():
    if 'email' in session:
        # get account info and check if account holder is student or not
        accountInfo = getAccountInfo()
        if accountInfo[0][3] == 'student':
            marks = getStudentMarks()
            if request.method == "POST":
                selectList = parseGrade(request.form["type"])
                reason = request.form["reason"]
                assesment = selectList[0]
                uname = session['email']
                grade = selectList[1]
                sql = """
                INSERT INTO Remark_Requests (user_name,assesment,
                reason,grade) VALUES (?,?,?,?);
                """

                data = [uname, assesment, reason, grade]
                db = get_db()
                res = db.execute(sql, data)
                db.commit()
                flash("Your remark request was submitted!", category="success")
            return render_template("studentMark.html", marks=marks)
        # account holder is inst show inst view
        elif accountInfo[0][3] == 'instructor':
            allMarks = getAllMark()
            if request.method == 'POST':
                grade = request.form["grade"]
                gradeFor = request.form["student"]
                aName = request.form["assessment"]
                sql = """
              INSERT INTO Marks (uname,assessment,mark) VALUES (?,?,?);
          """
                data = [gradeFor, aName, grade]
                db = get_db()
                res = db.execute(sql, data)
                db.commit()

                flash("Your regrade was submitted!", category="success")
            return render_template("instGrades.html", allMarks=allMarks)
    return redirect(url_for("login"))


# route remark page
@app.route("/remarks", methods=['GET', 'POST'])
def remark():
    if 'email' in session:
        # get account info and check if account holder is student or not
        accountInfo = getAccountInfo()
        print(accountInfo[0][3])
        if accountInfo[0][3] == 'instructor':
            remarks = getRemarkReq()
            if request.method == 'POST':
                newGrade = request.form["newMark"]
                regradeFor = request.form["regradeFor"]
                asName = request.form["regradeAs"]
                sql = """
                    UPDATE Marks SET mark = ? WHERE uname = ?
                    AND assessment = ?;
                    """
                data = [newGrade, regradeFor, asName]
                db = get_db()
                res = db.execute(sql, data)
                db.commit()
                secondSql = """
                  UPDATE Remark_Requests SET grade = ? WHERE user_name = ?
                  AND assesment = ?;
                  """
                res = db.execute(secondSql, data)
                db.commit()
                flash("Your regrade was submitted!", category="success")
            return render_template("remarkReqs.html", remarks=remarks)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1')
    # for mobile
    # app.run(debug=True, host='0.0.0.0')
