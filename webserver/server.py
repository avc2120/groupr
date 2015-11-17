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

@app.route('/dashboard/', methods=['GET','POST'])
def home():
  if session.get('email') == None:
    return redirect(url_for('index'))  

  results = []
  if request.method == 'POST':
    query = request.form["query"]
    cursor = g.conn.execute("SELECT * FROM groups;")
    for item in cursor:
      if query.lower() in item['group_name'].lower() and item['status'] == 'open':
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

    requests_admin = []
    query = "SELECT designate_admin.old_admin, designate_admin.group_id, groups.group_name FROM designate_admin INNER JOIN groups ON designate_admin.group_id = groups.group_id WHERE designate_admin.new_admin=%s"
    cursor = g.conn.execute(query, (session['email'],))
    for item in cursor.fetchall():
      a = {}
      a['old_admin'] = item['old_admin']
      a['group_name'] = item['group_name']
      a['group_id'] = item['group_id']
      requests_admin.append(a)

    requests = []
    query = "SELECT requests_join.group_id, requests_join.message, groups.group_name, requests_join.user_email FROM requests_join INNER JOIN groups ON requests_join.group_id = groups.group_id WHERE requests_join.user_email=%s AND requests_join.direction = %s;"
    cursor = g.conn.execute(query, (session['email'], 'group_to_user'))
    for item in cursor.fetchall():
      r = {}
      r['group_id'] = item['group_id']
      r['message'] = item['message']
      r['group_name'] = item['group_name'] 
      requests.append(r)

    return(render_template('home.html', results=results, requests_admin=requests_admin, user_email = session['email'], name=session['username'], groups=cur_group_data, requests=requests))


  requests_admin = []
  query = "SELECT designate_admin.old_admin, designate_admin.group_id, groups.group_name FROM designate_admin INNER JOIN groups ON designate_admin.group_id = groups.group_id WHERE designate_admin.new_admin=%s"
  cursor = g.conn.execute(query, (session['email'],))
  for item in cursor.fetchall():
    a = {}
    a['old_admin'] = item['old_admin']
    a['group_name'] = item['group_name']
    a['group_id'] = item['group_id']
    requests_admin.append(a)

  requests = []
  query = "SELECT requests_join.group_id, requests_join.message, groups.group_name, requests_join.user_email FROM requests_join INNER JOIN groups ON requests_join.group_id = groups.group_id WHERE requests_join.user_email=%s AND requests_join.direction = %s;"
  cursor = g.conn.execute(query, (session['email'], 'group_to_user'))
  for item in cursor.fetchall():
    r = {}
    r['group_id'] = item['group_id']
    r['message'] = item['message']
    r['group_name'] = item['group_name'] 
    requests.append(r)

  return render_template('home.html', requests_admin=requests_admin, user_email = session['email'], name=session['username'], groups=cur_group_data, requests=requests)

@app.route('/profile/')
def my_profile():
  if session.get('email') == None:
    return redirect(url_for('index'))  
  return render_template('myprofile.html', email = session['email'], username = session['username'], major = session['major'], gender = session['gender'], year = session['year'], housing = session['housing'], description=session['description'], groups=cur_group_data)

@app.route('/profile/<user_email>', methods=['GET'])
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

def get_group_member_number(group_id):
  query = """SELECT count(*) FROM belongs_to WHERE group_id=%s;"""
  cursor = g.conn.execute(query, (group_id,))
  for result in cursor.fetchall():
    return result['count']  

@app.route("/creategroup/", methods=["POST", "GET"])
def createGroup():
  global g, cur_group_data
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

  group_id = str(rand_id())
  group_name = request.form.get('group_name')
  group_des = request.form.get('description')
  is_unlimited = request.form.get('is_unlimited')
  group_lim = request.form.get('limit')
  group_status = request.form.get('optionsRadios')
  print is_unlimited
  if(is_unlimited == None):
    is_limited = True
  else:
    is_limited = False
  if(group_lim == ''):
    group_lim = 1000

  print group_name, group_des, group_lim, group_status
  print group_id, group_name, session["email"], group_des, group_lim, group_status
  query = "INSERT INTO groups VALUES(%s,%s,%s,%s,%s,%s,%s);"
  engine.execute(query, (group_id, session["email"], group_des, str(group_lim), is_limited, group_status, group_name))
  print "Successfully created group!"
  query = "INSERT INTO belongs_to VALUES(%s,%s);"
  engine.execute(query, (session['email'], group_id))
  print "Successfully belongs to group"

  query = "INSERT INTO containing VALUES (%s, %s);"
  print request.form.get('section'), group_id
  engine.execute(query, (request.form.get('section'), group_id))
  print "Successfully added to containing"
  g_dict = {}
  g_dict['group_id'] = int(group_id)
  g_dict['group_name'] = group_name
  g_dict['user_email'] = session['email']
  g_dict['description'] = group_des
  g_dict['size_limit'] = int(group_lim)
  g_dict['is_limited'] = is_limited
  cur_group_data.append(g_dict)

  print cur_group_data
  return redirect(url_for("group", group_id=group_id))

@app.route('/manage_group/<int:group_id>/', methods=['GET','POST'])
def manage_group(group_id):
  global g, cur_group_data
  if session.get('email') == None:
    return redirect(url_for('index'))

  for ind, group in enumerate(cur_group_data):
    if group['group_id'] == group_id:
      g_dict = cur_group_data[ind]
      break

  if g_dict['user_email'] != session['email']:
    flash('You do not have permission to access this page')
    return redirect(url_for('home'))

  #get list of members
  members = []
  query = """SELECT user_email, name FROM users WHERE user_email IN (SELECT user_email FROM belongs_to WHERE group_id=%s);"""
  cursor = g.conn.execute(query, (group_id,))
  results = cursor.fetchall()
  for item in results:
    u_d = {}
    u_d['user_email'] = item['user_email']
    u_d['name'] = item['name']
    if item['user_email'] == session['email']:
      #don't add self to members list
      continue 
    members.append(u_d)  

  is_alone = False
  if members == []:
    is_alone = True

  if request.method == 'POST':
    is_unlimited = request.form.get('is_unlimited')
    group_lim = request.form.get('limit')

    if(is_unlimited == None):
      num_members = get_group_member_number(group_id)
      if int(group_lim) < num_members:
        flash('You cannot change group size to below the current number of members!', 'danger')
      else:
        query = "UPDATE groups SET is_limited=%s, size_limit=%s WHERE group_id=%s;"
        g.conn.execute(query, (True,str(group_lim),str(group_id)))
        for group in cur_group_data:
          if group['group_id'] == int(group_id):
            group['is_limited'] = True
            group['size_limit'] = int(group_lim)
        flash('successfully changed group size limit','success')        
    else:
      query = "UPDATE groups SET is_limited=%s WHERE group_id=%s;"
      g.conn.execute(query, (False,str(group_id)))
      if group['group_id'] == group_id:
        group['is_limited'] = False
      flash('successfully changed group size limit','success')
    return redirect(url_for('manage_group', group_id=group_id))


  requests = []
  query = "SELECT requests_join.group_id, requests_join.message, users.name, requests_join.user_email FROM requests_join INNER JOIN users ON requests_join.user_email = users.user_email WHERE requests_join.group_id=%s AND requests_join.direction = %s;"
  cursor = g.conn.execute(query, (str(group_id), 'user_to_group'))
  for item in cursor.fetchall():
    r = {}
    r['name'] = item['name']
    r['user_email'] = item['user_email']
    r['message'] = item['message']
    requests.append(r)

  return(render_template('manage-group.html', is_alone=is_alone, group=g_dict, groups=cur_group_data, requests=requests, member_list=members))

@app.route('/delete_group/<int:group_id>')
def delete_group(group_id):
  #check if session[''] is group_id['admin']
  #delete from cur_group_data, containing, belongs_to, then groups
  global g, cur_group_data
  if session.get('email') == None:
    return redirect(url_for('index'))

  for ind, group in enumerate(cur_group_data):
    if group['group_id'] == int(group_id):
      g_dict = cur_group_data[ind]
      del cur_group_data[ind]
      break

  if g_dict['user_email'] != session['email']:
    flash('You do not have permission to access this page')
    return redirect(url_for('home'))

  q = "DELETE FROM containing WHERE group_id=%s"
  g.conn.execute(q,(str(group_id),))

  q = "DELETE FROM belongs_to WHERE group_id=%s"
  g.conn.execute(q,(str(group_id),))

  q = "DELETE FROM groups WHERE group_id=%s"
  g.conn.execute(q,(str(group_id),))

  flash('Successfully deleted group!', 'success')
  return redirect(url_for('home'))


@app.route('/leave_group/<int:group_id>/')
def leave_group(group_id):
  global g, cur_group_data
  if session.get('email') == None:
    return redirect(url_for('index'))
  query = "DELETE FROM belongs_to WHERE belongs_to.group_id = %s AND belongs_to.user_email = %s;"
  g.conn.execute(query, (str(group_id), session['email']))
  found_group = False
  for ind, group in enumerate(cur_group_data):
    if(group_id == group['group_id']):
      name = group['group_name']
      del cur_group_data[ind]
      flash('Successfully Left ' + name + '!', "success")
      found_group = True
      break
  if(found_group == False):
    flash('Something came up!', "danger")

  return redirect(url_for("home"))

@app.route('/group/<int:group_id>', methods=['GET','POST'])
def group(group_id):
  global g, cur_group_data
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
    print(group)
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
      g_dict['is_limited'] = item['is_limited']
      g_dict['size_limit'] = item['size_limit']
      g_dict['in_users_groups'] = False
      for group in cur_group_data:
        if item['group_id'] == group['group_id']:
          g_dict['in_users_groups'] = True
          break
      g_dict['joinable'] = True
      if g_dict['in_users_groups'] == False and g_dict['is_limited'] == True:
        number = get_group_member_number(item['group_id'])
        if number >= g_dict['size_limit']:
          g_dict['joinable'] = False    
                   
      group_list.append(g_dict)
  
  return render_template('section.html', groups=cur_group_data, group_list=group_list, course_id=course_id, call_number=call_number, course_title=course_title)

@app.route('/user_to_group_request2/<int:group_id>/<int:course_id>/<int:call_number>', methods=['POST'])
def user_to_group_request2(group_id,course_id,call_number):
  message = request.form["message-" + str(group_id)]
  query = "SELECT * from requests_join WHERE requests_join.user_email = %s AND requests_join.group_id = %s;"
  cursor = g.conn.execute(query, (session['email'], str(group_id)))
  if len(cursor.fetchall()) > 0:
    for item in cursor.fetchall():
      if item['direction'] == 'group_to_user':
        flash("A request has already been sent from this group to you!", "danger")
      else:
        flash("Your request to join this group is pending!", "danger")
  else:
    query = "INSERT INTO requests_join VALUES(%s,%s,%s,%s);"
    g.conn.execute(query, (session['email'], str(group_id), message, 'user_to_group'))
    flash('Successfully Sent Request to Join Group', 'success')

  return redirect(url_for('section', course_id=course_id, call_number=call_number))

@app.route('/group_to_user_request/<user_email>', methods=['POST'])
def group_to_user_request(user_email):
  group_id = request.form['whichgroup']
  message = request.form['message']
  query = "SELECT * from requests_join WHERE requests_join.user_email = %s AND requests_join.group_id = %s;"
  cursor = g.conn.execute(query, (user_email, str(group_id)))
  if len(cursor.fetchall()) > 0:
    flash('A request has already been sent from this user to the selected group!', 'danger')  
  else:
    query = "INSERT INTO requests_join VALUES(%s,%s,%s,%s);"
    g.conn.execute(query, (user_email, str(group_id), message, 'group_to_user'))
    flash('Successfully sent request', 'success')    
  return redirect(url_for('profile', user_email=user_email))

@app.route('/accept_request_from_user/<int:group_id>/<user_email>')
def accept_request_from_user(group_id,user_email):
  global g, cur_group_data
  if session.get('email') == None:
    return redirect(url_for('index'))

  for ind, group in enumerate(cur_group_data):
    if group['group_id'] == group_id:
      g_dict = cur_group_data[ind]
      break

  if g_dict['user_email'] != session['email']:
    flash('You do not have permission to access this page')
    return redirect(url_for('home')) 

  query = "SELECT * FROM groups WHERE groups.group_id =%s;"
  cursor = g.conn.execute(query, (group_id,))
  result = cursor.fetchone()
  g_dict = {}
  g_dict['group_id'] = int(group_id)
  g_dict['group_name'] = result['group_name']
  g_dict['user_email'] = result['user_email']
  g_dict['description'] = result['description']
  g_dict['size_limit'] = result['size_limit']
  g_dict['is_limited'] = result['is_limited']

  if(result['is_limited'] == True and get_group_member_number(group_id) >= result['size_limit']):
    flash('Group is at Capacity', 'warning')
  else:
    flash('Accepted Member Request','success')
    query = "INSERT INTO belongs_to VALUES(%s, %s);"
    g.conn.execute(query, (user_email, str(group_id)))
    print 'Successfully accepted request'

    query = "DELETE FROM requests_join WHERE requests_join.user_email = %s AND requests_join.group_id = %s;"
    g.conn.execute(query, (user_email, str(group_id)))
    print 'Successfully deleted request'

  return redirect(url_for("manage_group", group_id=group_id))

@app.route('/decline_request_from_user/<int:group_id>/<user_email>')
def decline_request_from_user(group_id,user_email):
  if session.get('email') == None:
    return redirect(url_for('index'))

  for ind, group in enumerate(cur_group_data):
    if group['group_id'] == group_id:
      g_dict = cur_group_data[ind]
      break

  if g_dict['user_email'] != session['email']:
    flash('You do not have permission to access this page')
    return redirect(url_for('home'))

  flash('Declined Group Request','danger')
  query = "DELETE FROM requests_join WHERE requests_join.user_email = %s AND requests_join.group_id = %s;"
  g.conn.execute(query, (user_email, str(group_id)))
  print 'Successfully deleted request'
  return redirect(url_for("manage_group", group_id=group_id))

@app.route('/kick_member/<int:group_id>/<user_email>')
def kick_member(group_id,user_email):
  if session.get('email') == None:
    return redirect(url_for('index'))

  for ind, group in enumerate(cur_group_data):
    if group['group_id'] == group_id:
      g_dict = cur_group_data[ind]
      break

  if g_dict['user_email'] != session['email']:
    flash('You do not have permission to access this page')
    return redirect(url_for('home'))

  query = "DELETE FROM belongs_to WHERE user_email=%s AND group_id=%s;"
  g.conn.execute(query, (user_email,str(group_id)))
  flash('Successfully kicked member', 'success')
  return redirect(url_for("manage_group", group_id=group_id))

@app.route('/make_admin/<int:group_id>/<new_admin>')
def make_admin(group_id,new_admin):
  if session.get('email') == None:
    return redirect(url_for('index'))

  for ind, group in enumerate(cur_group_data):
    if group['group_id'] == group_id:
      g_dict = cur_group_data[ind]
      break

  if g_dict['user_email'] != session['email']:
    flash('You do not have permission to access this page')
    return redirect(url_for('home'))

  query = "SELECT * FROM designate_admin WHERE old_admin=%s AND new_admin=%s AND group_id=%s;"
  cursor = g.conn.execute(query,(session['email'],new_admin,str(group_id)))
  if len(cursor.fetchall()) > 0:
    flash('You have already sent the admin designation request.', 'danger')
  else:
    q = "INSERT INTO designate_admin VALUES(%s,%s,%s);"
    g.conn.execute(q,(str(group_id),session['email'],new_admin))
    flash('Successfully sent admin designation request!', 'success')

  return redirect(url_for("manage_group", group_id=group_id))

@app.route('/accept_request/<int:group_id>', methods=["GET"])
def accept_request(group_id):
  global g, cur_group_data
  query = "SELECT * FROM groups WHERE groups.group_id =%s;"
  cursor = g.conn.execute(query, (group_id,))
  result = cursor.fetchone()
  g_dict = {}
  g_dict['group_id'] = int(group_id)
  g_dict['group_name'] = result['group_name']
  g_dict['user_email'] = result['user_email']
  g_dict['description'] = result['description']
  g_dict['size_limit'] = result['size_limit']
  g_dict['is_limited'] = result['is_limited']
  cur_group_data.append(g_dict)
  if(result['is_limited'] == True and get_group_member_number(group_id) >= result['size_limit']):
    flash('Group is at Capacity', 'warning')
  else:
    flash('Accepted Group Request','success')
    query = "INSERT INTO belongs_to VALUES(%s, %s);"
    g.conn.execute(query, (session['email'], str(group_id)))
    print 'Successfully accepted request'

    query = "DELETE FROM requests_join WHERE requests_join.user_email = %s AND requests_join.group_id = %s;"
    g.conn.execute(query, (session['email'], str(group_id)))
    print 'Successfully deleted request'
  return redirect(url_for("home"))

@app.route('/decline_request/<int:group_id>', methods=["GET"])
def decline_request(group_id):
  flash('Declined Group Request','danger')
  query = "DELETE FROM requests_join WHERE requests_join.user_email = %s AND requests_join.group_id = %s;"
  g.conn.execute(query, (session['email'], str(group_id)))
  print 'Successfully deleted request'
  return redirect(url_for("home"))

@app.route('/accept_admin/<int:group_id>', methods=["GET"])
def accept_admin(group_id):
  global g, cur_group_data
  for group in cur_group_data:
    if group['group_id'] == int(group_id):
      group['user_email'] = session['email']
  query = "UPDATE groups SET user_email = %s WHERE group_id = %s;"
  g.conn.execute(query, (session['email'], str(group_id)))
  flash('Accepted Admin Request','success')
  print 'Successfully accepted request'

  query = "DELETE FROM designate_admin WHERE designate_admin.group_id = %s;"
  g.conn.execute(query, (str(group_id),))
  print 'Successfully deleted request'
  for group in cur_group_data:
    if group['group_id'] == group_id:
      group['user_email'] = session['email']
  return redirect(url_for("home"))

@app.route('/decline_admin/<int:group_id>', methods=["GET"])
def decline_admin(group_id):
  flash('Declined Admin Request','danger')
  query = "DELETE FROM designate_admin WHERE designate_admin.group_id = %s;"
  g.conn.execute(query, (str(group_id),))
  print 'Successfully deleted request'
  return redirect(url_for("home"))

@app.route('/user_to_group_request/<int:group_id>', methods=["POST"])
def user_to_group_request(group_id):
  message = request.form["message-" + str(group_id)]
  print message
  query = "SELECT * from requests_join WHERE requests_join.user_email = %s AND requests_join.group_id = %s;"
  cursor = g.conn.execute(query, (session['email'], str(group_id)))
  if len(cursor.fetchall()) > 0:
    for item in cursor.fetchall():
      if item['direction'] == 'group_to_user':
        flash("A request has already been sent from this group to you!", "danger")
      else:
        flash("Your request to join this group is pending!", 'danger')
  else:
    query = "INSERT INTO requests_join VALUES(%s,%s,%s,%s);"
    g.conn.execute(query, (session['email'], str(group_id), message, 'user_to_group'))
    flash('Successfully Sent Request to Join Group', 'success')
  return redirect(url_for('home'))

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
