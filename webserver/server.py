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

# DATABASEURI = "sqlite:///groupr.db"
DATABASEURI = 'postgresql://avc2120:710@w4111db1.cloudapp.net:5432/proj1part2'
engine = create_engine(DATABASEURI)
#setup.dataSetup(engine)
# cursor = engine.execute("SELECT * FROM groups;")
# count = 0
# for item in cursor:
#   count = m.max(count, int(item['group_id']))

# group_id = count
# groupid_postid = {}
# cur_group_id = 0

cur_group_data = []

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
  if g:
    print(g)
    print('g is printed above')

  if request.method == "POST":
    email = request.form["email"]
    query = "SELECT * FROM users WHERE user_email=%s;"
    cursor = g.conn.execute(query, (email,))
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
    query = "INSERT INTO users VALUES(%s,%s,%s,%s," + str(year) + ",%s,%s);"
    g.conn.execute(query, (email, username, major, gender, description, housing))
    print "Sucessfully Created New Account"
    return redirect(url_for('home'))
  else:
    return render_template("index.html")

@app.route("/login/", methods=["POST", "GET"])
def login():
  global cur_group_data, g

  if request.method == "POST":
    email = request.form["email"]
    username = request.form["username"]
    query = """SELECT * FROM users WHERE user_email=%s AND name=%s;"""
    cursor = g.conn.execute(query, (email, username))
    results = cursor.fetchall()
    print len(results)
    if len(results) == 1:  
      print results
      result = results[0]
      session["email"] = email
      session["username"] = username
      session["major"] = result["major"]
      session["gender"] = result["gender"]
      session["year"] = int(result["year"])
      session["housing"] = result["housing"]
      session['description'] = result['description']
      
      cursor = g.conn.execute("""SELECT group_id FROM belongs_to WHERE user_email=%s""",(email,))
      results = cursor.fetchall()
      for item in results:
        print(item)
        cursor2 = g.conn.execute("""SELECT * FROM groups WHERE group_id=%s""",(str(item[0]),))
        results2 = cursor2.fetchall()
        for item2 in results2:
          print(item2)
          g = {}
          result2 = results2[0]
          g['group_id'] = result2['group_id']
          print(result2['group_id'])
          print(result2['user_email'])
          print(result2['description'])
          print(result2['size_limit'])
          print(result2['is_limited'])
          g['group_name'] = result2['group_name']
          g['user_email'] = result2['user_email']
          g['description'] = result2['description']
          g['size_limit'] = result2['size_limit']
          g['is_limited'] = result2['is_limited']
          g['status'] = result2['status']
          cur_group_data.append(g)

      return redirect(url_for('home'))
    else:
      return render_template("login.html", error="Invalid Email and/or Username")
  else:
    return render_template("login.html", error="")

@app.route('/dashboard/')
def home():
  print g
  print('g is printed above')
  if session.get('email') == None:
    return redirect(url_for('index'))  
  return render_template('home.html', user_email = session['email'], groups=cur_group_data)

@app.route('/profile/')
def my_profile():
  print g
  print('g is printed above profile')
  if session.get('email') == None:
    return redirect(url_for('index'))  
  return render_template('myprofile.html', email = session['email'], username = session['username'], major = session['major'], gender = session['gender'], year = session['year'], housing = session['housing'], description=session['description'], groups=cur_group_data)

@app.route('/signout/')
def signout():
  session.pop('username', None)
  session.pop('email', None)
  return redirect(url_for('index'))

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
  
@app.route("/creategroup/", methods=["POST", "GET"])
def createGroup():
  if session.get('email') == None:
    return redirect(url_for('index'))

  if request.method == 'GET':
    return render_template("creategroup.html")

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
  query = "INSERT INTO groups VALUES(%d,%s,%s,%s,%d,%r,%s);"
  engine.execute(query, (int(group_id), group_name, session["email"], group_des, int(group_lim), is_limited, group_status_string))
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
  query = "INSERT INTO board_posted VALUES(%d,%d,%r,%s,%s);"
  engine.execute(query, (int(post_id), int(cur_group_id), date_time, post, session["email"]))
  cursor = engine.execute("SELECT * FROM groups, board_posted ON groups.group_id = board_posted.group_id AND groups.group_id = %d", cur_group_id)
  result = []
  for item in cursor:
    print item
    group_name = item["group_name"]
    group_des = item["description"]
    result.append(item)
  cursor.close()
  context = dict( data = result )
  return render_template("group.html", user_email=session["email"], group_name=group_name, group_description=group_des, group_admin=session["email"], **context)

@app.route('/manage_group/<int:group_id>')
def manage_group(group_id):
  if session.get('email') == None:
    return redirect(url_for('index'))

  print('hello')

@app.route('/group/<int:group_id>', methods=['GET','POST'])
def group(group_id):
  if session.get('email') == None:
    return redirect(url_for('index'))

  for ind, group in enumerate(cur_group_data):
    if group['group_id'] == group_id:
      g_dict = cur_group_data[ind]
      break
    if ind == len(cur_group_data)-1 and group_id != group['group_id']: 
      print('You are looking for a group with an id that doesnt exist.')
      return redirect(url_for('index'))

  is_admin = False
  if g_dict['user_email'] == session['email']:
    is_admin = True

  return render_template('group.html', group=g_dict, groups=cur_group_data)

@app.route('/course/<int:course_id>', methods=['GET','POST'])
def course(course_id):
  if session.get('email') == None:
    return redirect(url_for('index'))

  #don't see your course? add it
  if request.method == 'POST':
    print('hello')
    return redirect(url_for('course', course_id=course_id))

  print('hello')
  return render_template('course.html', groups=cur_group_data)

@app.route('/course/<int:course_id>/<int:call_number>', methods=['GET','POST'])
def section(course_id,call_number):
  if session.get('email') == None:
    return redirect(url_for('index'))  
  #don't see your section? add it
  if request.method == 'POST':
    print('hello')
    return redirect(url_for('section',course_id=course_id,call_number=call_number))
  
  print('hello')
  return render_template('section.html', groups=cur_group_data)

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
