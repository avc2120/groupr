#!/usr/bin/env python2.7
#########################################
#GROUPR:
#COMS W4111: Databases
#Names: Alice Chang, Mango Yumeng Liao
#########################################
import math
import os
import datetime
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DATABASEURI = "sqlite:///groupr.db"

engine = create_engine(DATABASEURI)
Session = sessionmaker(bind=engine)
Session = Session()

cursor = engine.execute("SELECT * FROM groups;")
count = 0
for item in cursor:
  count = math.max(count, item['group_id'])

group_id = count
groupid_postid = {}
my_email = ""
my_username = ""
my_major = ""
my_gender = ""
my_year = 0
my_housing = ""
cur_group_id = 0
#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
# engine.execute("""DROP TABLE IF EXISTS users;""")
# engine.execute("""DROP TABLE IF EXISTS groups;""")
# engine.execute("""DROP TABLE IF EXISTS board_posted;""")

# engine.execute("""CREATE TABLE users(
#   user_email text, 
#   name text,
#   major text, 
#   gender text,
#   year int CHECK (year > 0 AND year <=5), /*year 5 = all graduate students*/
#   description text, 
#   housing text,
#   PRIMARY KEY (user_email)
#   );""")
# engine.execute("""CREATE TABLE groups(
#   group_id int,
#   group_name text,
#   user_email text,
#   description text,
#   size_limit int,
#   is_limited boolean,
#   status text CHECK (status = 'open' OR status = 'closed'),
#   FOREIGN KEY (user_email) REFERENCES users,
#   PRIMARY KEY(group_id)
#   );""")
# engine.execute("""CREATE table board_posted(
#   post_id int,
#   group_id int,
#   date_time timestamp,
#   message text,
#   user_email text NOT NULL,
#   PRIMARY KEY(post_id, user_email),
#   FOREIGN KEY(group_id) REFERENCES groups,
#   FOREIGN KEY(user_email) REFERENCES users
#     ON DELETE CASCADE
#   );""")

# END SQLITE SETUP CODE
#

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

@app.route("/signup/", methods=["POST", "GET"])
def signup():
  email = request.args["email"]
  username = request.args["username"]
  major = request.args["major"]
  gender = request.args["gender"]
  year = request.args["year"]
  description = request.args["description"]
  housing = request.args["housing"]

  cursor = g.conn.execute("SELECT * FROM users WHERE user_email=?;", email)
  # print session.query(users).filter_by(user_email=email)

  count = 0
  for item in cursor:
    count += 1
  if count == 1:
    return render_template("index.html", invalid_email="This email already has an account")
  global my_email, my_username, my_major, my_gender, my_year, my_housing
  my_email = email
  my_username = username
  my_major = major
  my_gender = gender
  my_year = int(year)
  my_housing = housing

  print email, username, gender, major, int(year), housing, description
  engine.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?);", email, username, major, gender, int(year), description, housing)
  #engine.execute(text('INSERT INTO users(user_email, name, gender, major, year, description, housing) VALUES(:mail, :name, :maj, :gen, :yr, :des, :house);'), mail = email, name = username, maj = major, gen = gender, yr =  4, des = description, house = housing)
  return render_template("home.html", user_email=email)

@app.route("/getLogin/", methods=["POST","GET"])
def getLogin():
  return render_template("login.html", error="")

@app.route("/login/", methods=["POST", "GET"])
def login():
  email = request.args["email"]
  username = request.args["username"]
  print email, username
  #print ("SELECT * FROM users WHERE users.user_email = '{}';".format(email))
  cursor = g.conn.execute("""SELECT * FROM users WHERE user_email=? AND name=?;""", email, username)
  print "hello"
  count = 0

  global my_email, my_username, my_major, my_gender, my_year, my_housing
  for result in cursor:
    my_major = result["major"]
    my_gender = result["gender"]
    my_year = int(result["year"])
    my_housing = result["housing"]
    count += 1


  if count == 1:
    my_email = email
    return render_template("home.html", user_email=email)
  else:
    return render_template("login.html", error="Invalid Email and/or Username")

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
  global group_id, groupid_postid, my_email, cur_group_id
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
  print group_id, group_name, my_email, group_des, int(group_lim), group_status_string
  engine.execute("INSERT INTO groups VALUES(?,?,?,?,?,?,?);", int(group_id), group_name, my_email, group_des, int(group_lim), is_limited, group_status_string)
  print "Success!"
  if(is_limited):
    return render_template("group.html", user_email=my_email, 
      group_name=group_name, group_description=group_des, group_admin=my_email, size_limit=group_lim)
  else:
    return render_template("group.html", user_email=my_email, 
      group_name=group_name, group_description=group_des, group_admin=my_email)

@app.route("/gotogroup/", methods=["POST","GET"])
def postInGroup():
  post = request.args["post"]
  groupid_postid[cur_group_id] += 1
  post_id = groupid_postid[cur_group_id]
  date_time = datetime.datetime.now()
  engine.execute("INSERT INTO board_posted VALUES(?,?,?,?,?);", post_id, cur_group_id, date_time, post, my_email)
  print "succesfully inserted"
  # cursor = engine.execute("SELECT * FROM board_posted WHERE group_id = ?", cur_group_id)
  cursor = engine.execute("SELECT * FROM groups, board_posted ON groups.group_id = board_posted.group_id AND groups.group_id = ?", cur_group_id)
  print "succesfully queried"
  result = []
  for item in cursor:
    print item
    group_name = item["group_name"]
    group_des = item["description"]
    result.append(item["message"])
  cursor.close()
  print "group information: " , group_name, group_des
  context = dict( data = result )
  return render_template("group.html", user_email=my_email, group_name=group_name, group_description=group_des, group_admin=my_email, **context)

# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
# 
@app.route('/', methods=["POST", "GET"])
def index():
  return render_template("index.html")

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
