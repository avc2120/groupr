#!/usr/bin/env python2.7
#########################################
#GROUPR:
#COMS W4111: Databases
#Names: Alice Chang, Mango Yumeng Liao
#########################################
import setup
import math as m
import os
import datetime
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, escape

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)

DATABASEURI = "sqlite:///groupr.db"
engine = create_engine(DATABASEURI)
#setup.dataSetup(engine)
cursor = engine.execute("SELECT * FROM groups;")
count = 0
for item in cursor:
  count = m.max(count, int(item['group_id']))

group_id = count
groupid_postid = {}
cur_group_id = 0

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/', methods=["POST", "GET"])
def index():
  if request.method == "POST":
    email = request.form["email"]
    print email
    cursor = g.conn.execute("SELECT * FROM users WHERE user_email=?;", email)
    if len(cursor.fetchall()) == 1:
      return render_template("index.html", error="This email already has an account")
    session["email"] = email
    session["username"] = username = request.form["username"]
    session["major"] = major = request.form["major"]
    session["gender"] = gender = request.form["gender"]
    session["year"] = year = int(request.form["year"])
    session["description"] = description = request.form["description"]
    session["housing"] = housing = request.form["housing"]

    my_args =  (email, username, gender, major, year, housing, description)
    if "" in my_args:
      return render_template("index.html", error="Please fill out all required fields" )
    engine.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?);", email, username, major, gender, year, description, housing)
    print "Sucessfully Created New Account"
    return render_template("home.html", user_email=email)
  else:
    return render_template("index.html")

@app.route("/login/", methods=["POST", "GET"])
def login():
  if request.method == "POST":
    session["email"] = email = request.form["email"]
    session["username"] = username = request.form["username"]
    cursor = g.conn.execute("""SELECT * FROM users WHERE user_email=? AND name=?;""", email, username)
    results = cursor.fetchall()
    print len(results)
    if len(results) == 1:  
      print results
      result = results[0]
      print result
      session["major"] = result["major"]
      session["gender"] = result["gender"]
      session["year"] = int(result["year"])
      session["housing"] = result["housing"]
      return render_template("home.html", user_email=email)
    else:
      return render_template("login.html", error="Invalid Email and/or Username")
  else:
    return render_template("login.html", error="")

@app.route("/logout/")
def logout():
  session.pop("username", None)
  session.pop("email", None)
  return redirect(url_for("index"))

@app.route("/search/", methods=["POST", "GET"])
def search():
  query = request.args["query"]
  print query
  cursor = g.conn.execute("SELECT * FROM groups;")
  results = []
  for item in cursor:
    if query.lower() in item['group_name'].lower():
      results.append(item)
  cursor.close()
  context = dict(data = results)
  return render_template("home.html", **context)

@app.route("/gotocreategroup/", methods=["POST", "GET"])
def goToCreateGroup():
  return render_template("creategroup.html")

@app.route("/creategroup/", methods=["POST", "GET"])
def createGroup():
  global group_id, groupid_postid, cur_group_id
  group_id += 1
  groupid_postid[group_id] = 0
  cur_group_id = group_id
  group_name = request.args["groupname"]
  group_des = request.args["description"]
  group_lim = int(request.args["limit"])
  group_status = request.args["status"]
  group_status_string = "closed"

  is_limited = True
  if(group_lim == None):
    is_limited = False
  if (group_status == "on"):
    group_status_string = "open"

  print group_name, group_des, group_lim, group_status
  print group_id, group_name, session["email"], group_des, int(group_lim), group_status_string
  engine.execute("INSERT INTO groups VALUES(?,?,?,?,?,?,?);", int(group_id), group_name, session["email"], group_des, int(group_lim), is_limited, group_status_string)
  print "Success!"
  if(is_limited):
    return render_template("group.html", user_email=session["email"], 
      group_name=group_name, group_description=group_des, group_admin=session["email"], size_limit=group_lim)
  else:
    return render_template("group.html", user_email=session["email"], 
      group_name=group_name, group_description=group_des, group_admin=session["email"])

@app.route("/gotogroup/", methods=["POST","GET"])
def postInGroup():
  post = request.args["post"]
  groupid_postid[cur_group_id] += 1
  post_id = groupid_postid[cur_group_id]
  date_time = datetime.datetime.now()
  engine.execute("INSERT INTO board_posted VALUES(?,?,?,?,?);", post_id, cur_group_id, date_time, post, session["email"])
  cursor = engine.execute("SELECT * FROM groups, board_posted ON groups.group_id = board_posted.group_id AND groups.group_id = ?", cur_group_id)
  result = []
  for item in cursor:
    print item
    group_name = item["group_name"]
    group_des = item["description"]
    result.append(item["message"])
  cursor.close()
  context = dict( data = result )
  return render_template("group.html", user_email=session["email"], group_name=group_name, group_description=group_des, group_admin=session["email"], **context)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
