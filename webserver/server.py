#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.

eugene wu 2015
"""

import os
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
#requests - global object that handles the current request
#g - global object

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

group_id = 0
my_email = ""
my_username = ""
my_major = ""
my_gender = ""
my_year = 0
my_housing = ""
#
# The following uses the sqlite3 database test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@w4111db1.cloudapp.net:5432/proj1part2
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@w4111db1.cloudapp.net:5432/proj1part2"

DATABASEURI = "sqlite:///groupr.db"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)
Session = sessionmaker(bind=engine)
Session = Session()

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
engine.execute("""DROP TABLE IF EXISTS users;""")
engine.execute("""DROP TABLE IF EXISTS groups;""")

engine.execute("""CREATE TABLE users(
  user_email text, 
  name text,
  major text, 
  gender text,
  year int CHECK (year > 0 AND year <=5), /*year 5 = all graduate students*/
  description text, 
  housing text,
  PRIMARY KEY (user_email)
  );""")
engine.execute("""CREATE TABLE groups(
  group_id int,
  group_name text,
  user_email text,
  description text,
  size_limit int,
  is_limited boolean,
  status text CHECK (status = 'open' OR status = 'closed'),
  FOREIGN KEY (user_email) REFERENCES users,
  PRIMARY KEY(group_id)
  );""")
# engine.execute("INSERT INTO groups VALUES(?,?,?,?,?,?,?);", 1, "Databases", "changvalice", "HI", 3, True , "open")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
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
    return render_template("home.html", user_email=email)
  else:
    return render_template("login.html", error="Invalid Email and/or Username")

@app.route("/search/", methods=["POST", "GET"])
def search():
  query = request.args["query"]
  print query
  cursor = g.conn.execute("""SELECT * FROM groups""")
  results = []
  for item in cursor:
    if query in item['description']:
      results.append(item['description'])

@app.route("/gotocreategroup/", methods=["POST", "GET"])
def goToCreateGroup():
  return render_template("creategroup.html")

@app.route("/creategroup/", methods=["POST", "GET"])
def createGroup():
  global group_id, my_email
  group_id += 1
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
#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a POST or GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
# 
@app.route('/', methods=["POST", "GET"])
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  # print request.args


  #
  # example of a database query
  #
  # cursor = g.conn.execute("SELECT name FROM test")
  # names = []
  # for result in cursor:
  #   names.append(result['name'])  # can also be accessed using result[0]
  # cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  # context = dict( data = names )


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
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