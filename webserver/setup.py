def dataSetup(engine):
	engine.execute("""DROP TABLE IF EXISTS users;""")
	engine.execute("""DROP TABLE IF EXISTS groups;""")
	engine.execute("""DROP TABLE IF EXISTS courses;""")
	engine.execute("""DROP TABLE IF EXISTS has_sections;""")
	engine.execute("""DROP TABLE IF EXISTS requests_join;""")
	engine.execute("""DROP TABLE IF EXISTS containing;""")
	engine.execute("""DROP TABLE IF EXISTS belongs_to;""")
	engine.execute("""DROP TABLE IF EXISTS board_posted;""")

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
	engine.execute("""CREATE TABLE courses(
	  course_title text,
	  course_id int,
	  term text,
	  department text,
	  PRIMARY KEY(course_id)
	  );""")
	engine.execute("""CREATE TABLE has_sections(
	  call_number int,
	  professor text,
	  course_id int,
	  PRIMARY KEY (call_number),
	  FOREIGN KEY (course_id) REFERENCES courses
	    ON DELETE NO ACTION
	  );""")
	engine.execute("""CREATE TABLE requests_join(
	  user_email text,
	  group_id int,
	  message text,
	  PRIMARY KEY (user_email, group_id),
	  FOREIGN KEY(user_email) REFERENCES users,
	  FOREIGN KEY(group_id) REFERENCES groups
	  );""")
	engine.execute("""CREATE TABLE containing(
	   call_number int,
	   group_id int, 
	   PRIMARY KEY(call_number, group_id),
	   FOREIGN KEY(call_number) REFERENCES has_sections,
	   FOREIGN KEY(group_id) REFERENCES groups
	   );""")
	engine.execute("""CREATE TABLE belongs_to(
	  user_email text,
	  group_id int,
	  PRIMARY KEY(user_email, group_id),
	  FOREIGN KEY(user_email) REFERENCES users,
	  FOREIGN KEY(group_id) REFERENCES groups
	  );""")
	engine.execute("""CREATE TABLE board_posted(
	  post_id int,
	  group_id int,
	  date_time timestamp,
	  message text,
	  user_email text NOT NULL,
	  PRIMARY KEY(post_id, user_email),
	  FOREIGN KEY(group_id) REFERENCES groups,
	  FOREIGN KEY(user_email) REFERENCES users
	    ON DELETE CASCADE
	  );""")