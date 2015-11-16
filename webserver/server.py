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
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, escape, flash
from random import randint

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

def rand_id():
  return randint(10000000,99999999)

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
  global g, cur_group_data
  if request.method == "POST":
    cur_group_data = []
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
    if len(results) == 1:  
      result = results[0]
      session["email"] = email
      session["username"] = username
      session["major"] = result["major"]
      session["gender"] = result["gender"]
      session["year"] = int(result["year"])
      session["housing"] = result["housing"]
      session['description'] = result['description']
      
      cur_group_data = []
      q= """SELECT group_id FROM belongs_to WHERE user_email=%s"""
      cursor = g.conn.execute(q,(email,))
      results = cursor.fetchall()
      for item in results:
        q2 = """SELECT * FROM groups WHERE group_id=%s"""
        cursor2 = g.conn.execute(q2,(str(item[0]),))
        results2 = cursor2.fetchall()
        for item2 in results2:
          g_dict = {}
          result2 = results2[0]
          g_dict['group_id'] = result2['group_id']
          g_dict['group_name'] = result2['group_name']
          g_dict['user_email'] = result2['user_email']
          g_dict['description'] = result2['description']
          g_dict['size_limit'] = result2['size_limit']
          g_dict['is_limited'] = result2['is_limited']
          g_dict['status'] = result2['status']
          cur_group_data.append(g_dict)

      #copy paste this to get rid of duplicates in cur_group_data
      {v['group_id']:v for v in cur_group_data}.values() 
      
      return redirect(url_for('home'))
    else:
      return render_template("login.html", error="Invalid Email and/or Username")
  else:
    return render_template("login.html", error="")

@app.route('/dashboard/')
def home():
  if session.get('email') == None:
    return redirect(url_for('index'))  
  return render_template('home.html', user_email = session['email'], name=session['username'], groups=cur_group_data)

@app.route('/profile/')
def my_profile():
  if session.get('email') == None:
    return redirect(url_for('index'))  
  return render_template('myprofile.html', email = session['email'], username = session['username'], major = session['major'], gender = session['gender'], year = session['year'], housing = session['housing'], description=session['description'], groups=cur_group_data)

@app.route('/profile/<user_email>')
def profile(user_email):
  global g, cur_group_data

  if session.get('email') == None:
    return redirect(url_for('index'))

  query = """SELECT * from users WHERE user_email=%s"""
  cursor = g.conn.execute(query, (user_email,))
  user_data = {}
  for item in cursor.fetchall():
    user_data['user_email'] = user_email
    user_data['name'] = item['name']
    user_data['major'] = item['major']
    user_data['gender'] = item['gender']
    user_data['year'] = item['year']
    user_data['description'] = item['description']
    user_data['housing'] = item['housing']

  is_me = False
  if user_data['user_email'] == session['email']:
    is_me = True

  is_admin = False
  admin_list = []
  for group in cur_group_data:
    if group['user_email'] == session['email']:
      is_admin=True
      admin_list.append(group)

  return render_template('profile.html', is_me=is_me, user=user_data, groups=cur_group_data, is_admin=is_admin, admin_list=admin_list)

@app.route("/browse_profiles/", methods=["GET"])
def browse_profiles():
  if session.get('email') == None:
    return redirect(url_for('index'))

  if request.method == "GET":
    cursor = g.conn.execute("SELECT * FROM users ORDER BY name ASC, user_email ASC;")
    user_list = []
    for item in cursor.fetchall():
      c = {}
      c['user_email'] = item['user_email']
      c['name'] = item['name']
      c['major'] = item['major']
      c['gender'] = item['gender']
      c['year'] = item['year']
      c['description'] = item['description']
      c['housing'] = item['housing']
      user_list.append(c)

    return render_template('browse-profiles.html', users=user_list, groups=cur_group_data)

@app.route('/signout/')
def signout():
  global cur_group_data, g
  session.pop('username', None)
  session.pop('email', None)
  cur_group_data = []
  return redirect(url_for('index'))

@app.route("/search/", methods=["POST", "GET"])
def search():
  if session.get('email') == None:
    return redirect(url_for('index'))

  query = request.args["query"]
  cursor = g.conn.execute("SELECT * FROM groups;")
  results = []
  for item in cursor:
    if query.lower() in item['group_name'].lower() and item['status'] == 'open':
      print(item)
      temp = {}
      temp['group_id'] = item['group_id']
      temp['group_name'] = item['group_name']
      temp['user_email'] = item['user_email']
      temp['description'] = item['description']
      temp['is_limited'] = item['is_limited']
      temp['size_limit'] = item['size_limit']
      temp['in_users_groups'] = False
      for group in cur_group_data:
        if item['group_id'] == group['group_id']:
          temp['in_users_groups'] = True
          break
      #check if 
      temp['joinable'] = True
      if temp['in_users_groups'] == False and temp['is_limited'] == True:
        number = get_group_member_number(item['group_id'])
        if number >= temp['size_limit']:
          temp['joinable'] = False

      results.append(temp)

  cursor.close()
  return render_template("home.html", groups=cur_group_data, user_email=session['email'], name=session['username'], results=results)

def get_group_member_number(group_id):
  query = """SELECT count(*) FROM belongs_to WHERE group_id=%s;"""
  cursor = g.conn.execute(query, (group_id,))
  for result in cursor.fetchall():
    return result['count']  

@app.route("/creategroup/", methods=["POST", "GET"])
def createGroup():
  if session.get('email') == None:
    return redirect(url_for('index'))

  if request.method == 'GET':
    query = "SELECT * FROM courses;"
    cursor = g.conn.execute(query)
    courses = []
    course_to_section_dict = {}
    for course in cursor.fetchall():
      course_dict = {}
      course_dict['course_id'] = course['course_id']
      course_dict['course_title'] = course['course_title']
      course_dict['term'] = course['term']
      courses.append(course_dict)
      query = "SELECT * from has_sections WHERE has_sections.course_id = %s;"
      cursor2 = g.conn.execute(query, (str(course['course_id']),))
      sections = []
      for section in cursor2.fetchall():
        section_dict = {}
        section_dict['professor'] = section['professor']
        section_dict['call_number'] = section['call_number']
        sections.append(section_dict)
      course_to_section_dict[course['course_id']] = sections
    return render_template("creategroup.html", groups=cur_group_data, courses=courses, c_to_s=course_to_section_dict)

  global group_id, groupid_postid, cur_group_id
  group_id = str(rand_id())
  group_name = request.form.get('group_name')
  group_des = request.form.get('description')
  is_unlimited = request.form.get('is_unlimited')
  group_lim = int(request.form.get('limit'))
  group_status = request.form.get('optionsRadios')

  is_limited = True
  if(is_unlimited == None):
    islimited = False

  print group_name, group_des, group_lim, group_status
  print group_id, group_name, session["email"], group_des, int(group_lim), group_status
  query = "INSERT INTO groups VALUES(%s,%s,%s,%s,%s,%s,%s);"
  engine.execute(query, (group_id, group_name, session["email"], group_des, group_lim, is_limited, group_status))
  print "Success!"

  if(is_limited):
    return render_template("group.html", user_email=session["email"], 
      group_name=group_name, group_description=group_des, group_admin=session["email"], size_limit=group_lim)
  else:
    return render_template("group.html", user_email=session["email"], 
      group_name=group_name, group_description=group_des, group_admin=session["email"])

@app.route('/manage_group/<int:group_id>/')
def manage_group(group_id):
  if session.get('email') == None:
    return redirect(url_for('index'))

  print('hello')

@app.route('/group/<int:group_id>', methods=['GET','POST'])
def group(group_id):
  if session.get('email') == None:
    return redirect(url_for('index'))

  #handles wall posts
  if request.method == 'POST':
    message = request.form['the-post']
    post_id = str(rand_id())
    user_email = session['email']
    group_id_str = str(group_id)
    date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print message
    print post_id
    print user_email
    print date_time
    query = "INSERT INTO board_posted VALUES(%s,%s,%s,%s,%s);"
    result = g.conn.execute(query, (post_id, group_id_str, date_time, message, user_email))
    flash('Successfully made post!')
    return redirect(url_for('group', group_id=group_id))
    

  # save on db queries by picking out correct data from data of all groups user belongs to
  for ind, group in enumerate(cur_group_data):
    if group['group_id'] == group_id:
      g_dict = cur_group_data[ind]
      break
    if ind == len(cur_group_data)-1 and group_id != group['group_id']: 
      print('You do not have permission to access this group or this group doesnt exist')
      return redirect(url_for('index'))

  is_admin = False
  if g_dict['user_email'] == session['email']:
    is_admin = True

  #get admin username
  cursor = g.conn.execute("""SELECT name FROM users WHERE user_email=%s;""", (g_dict['user_email'],))
  for item in cursor.fetchall():
    admin = item['name']

  #get course data
  classdata={}
  query = """SELECT call_number FROM containing WHERE group_id=%s;"""
  cursor = g.conn.execute(query, (group_id,))
  result1 = cursor.fetchall()
  for item in result1:
    classdata['call_number'] = item['call_number']
    q2 = """SELECT professor, course_id FROM has_sections WHERE call_number=%s;"""
    cursor2 = g.conn.execute(q2, (item['call_number'],))
    for item2 in cursor2.fetchall():
      classdata['prof'] = item2['professor']
      q3 = """SELECT course_title, term, department FROM courses WHERE course_id=%s;"""
      cursor3 = g.conn.execute(q3, (item2['course_id']))
      for item3 in cursor3.fetchall():
        classdata['course_title'] = item3['course_title']
        classdata['term'] = item3['term'] 
        classdata['department'] = item3['department']  

  #get list of members
  members = []
  query = """SELECT user_email, name FROM users WHERE user_email IN (SELECT user_email FROM belongs_to WHERE group_id=%s);"""
  cursor = g.conn.execute(query, (group_id,))
  results = cursor.fetchall()
  for item in results:
    u_d = {}
    u_d['user_email'] = item['user_email']
    u_d['name'] = item['name']
    members.append(u_d)

  #get board posts
  posts = []
  query = """SELECT * FROM board_posted WHERE group_id=%s ORDER BY date_time desc;"""
  cursor = g.conn.execute(query, (group_id,))
  results = cursor.fetchall()
  for item in results:
    p = {}
    p['date_time'] = item['date_time']
    p['message'] = item['message']
    p['poster'] = get_username(item['user_email']) 
    posts.append(p)

  return render_template('group.html', username=session['username'],posts=posts, admin=admin, members=members, group=g_dict, is_admin=is_admin, groups=cur_group_data, classdata=classdata)

def get_username(user_email):
  cursor = g.conn.execute("""SELECT name FROM users WHERE user_email=%s""", (user_email,))
  for item in cursor.fetchall():
    return item['name']

@app.route('/browse_groups', methods=['GET','POST'])
def browse_groups():
  if session.get('email') == None:
    return redirect(url_for('index'))

  #add courses
  if request.method == 'POST':
    course_id = str(rand_id())
    term = request.form['semester'] + ' ' + request.form['year'] 
    department = request.form['department']
    course_title = request.form['course_title']
    query = "INSERT INTO courses VALUES(%s,%s,%s,%s);"
    g.conn.execute(query, (course_title, course_id, term, department))
    flash('Successfully added course!')
    return(redirect(url_for('browse_groups')))

  cursor = g.conn.execute("SELECT * FROM courses ORDER BY course_title ASC;")
  course_list = []
  for item in cursor.fetchall():
    c = {}
    c['course_title'] = item['course_title']
    c['course_id'] = item['course_id']
    c['term'] = item['term']
    c['department'] = item['department']
    course_list.append(c)
    
  return render_template('browse-groups.html', courses=course_list, groups=cur_group_data)

@app.route('/course/<int:course_id>', methods=['GET','POST'])
def course(course_id):
  if session.get('email') == None:
    return redirect(url_for('index'))

  #don't see your section? add it
  if request.method == 'POST':
    call_number = request.form['call'] 
    professor = request.form['prof']
    query = "SELECT call_number FROM has_sections;"
    list_call_numbers = []
    cursor = g.conn.execute(query)
    for c_num in cursor.fetchall():
      list_call_numbers.append(c_num['call_number'])
    
    if (int(call_number)) in list_call_numbers:
      flash('This call number is registered with a section already!', 'danger')
      return redirect(url_for('course', course_id=course_id))

    query = "INSERT INTO has_sections VALUES(%s,%s,%s);"
    g.conn.execute(query, (call_number, professor, course_id))   
    flash('Section successfully added!', 'success')
    return redirect(url_for('course', course_id=course_id))

  query = "SELECT course_title FROM courses WHERE course_id=%s"
  cursor = g.conn.execute(query, (str(course_id),))
  for item in cursor.fetchall():
    course_name = item['course_title']

  query = "SELECT * FROM has_sections INNER JOIN courses ON has_sections.course_id = courses.course_id WHERE courses.course_id = %s;"
  cursor = g.conn.execute(query, (str(course_id),))
  section_list = []

  for item in cursor.fetchall():
    c = {}
    c['course_id'] = course_id
    c['call_number'] = item['call_number']
    c['professor'] = item['professor']
    section_list.append(c)

  return render_template('course.html', groups=cur_group_data, sections=section_list, course_name=course_name, course_id=course_id)

@app.route('/course/<int:course_id>/<int:call_number>', methods=['GET','POST'])
def section(course_id,call_number):
  if session.get('email') == None:
    return redirect(url_for('index'))  

  #don't see your section? add it
  if request.method == 'POST':
    return redirect(url_for('section', course_id=course_id, call_number=call_number))

  cursor = g.conn.execute("SELECT * FROM courses WHERE courses.course_id = %s", (str(course_id),))
  result = cursor.fetchone()
  course_title = result['course_title']


  query = "SELECT groups.group_id, groups.group_name, groups.user_email, groups.description, groups.is_limited, groups.size_limit FROM containing INNER JOIN groups ON containing.group_id = groups.group_id WHERE containing.call_number=%s AND groups.status=%s;"
  cursor = g.conn.execute(query, (str(call_number), 'open') )
  group_list = []
  for item in cursor.fetchall():
    cursor = g.conn.execute("SELECT * FROM belongs_to WHERE belongs_to.group_id = %s", (str(item['group_id']),))
    if (len(cursor.fetchall())< item['size_limit']) or (item['is_limited'] == False):
      g_dict = {}
      g_dict['group_id'] = item['group_id']
      g_dict['group_name'] = item['group_name']
      g_dict['user_email'] = item['user_email']
      g_dict['description'] = item['description']
      group_list.append(g_dict)
      print g_dict
  return render_template('section.html', groups=cur_group_data, group_list=group_list, course_id=course_id, call_number=call_number, course_title=course_title)


@app.route('/group_to_user_request', methods=['POST'])
def group_to_user_request(user_email):
  print('hello')
  #this needs to be writted with a redirect


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
