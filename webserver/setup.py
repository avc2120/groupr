def dataSetup(engine):
	engine.execute("""DROP TABLE IF EXISTS users;""")
	engine.execute("""DROP TABLE IF EXISTS groups;""")
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
	engine.execute("""CREATE table board_posted(
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