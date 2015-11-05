/* entities */
create table users(
  user_email text, 
  name text,
  major text, 
  gender text CHECK (gender = 'Female' OR gender = 'Male'), 
  year int CHECK (year > 0 AND year <=5), /*year 5 = all graduate students*/
  description text, 
  housing text,
  PRIMARY KEY (user_email)
  );
  
create table groups(
  group_id int,
  user_email text,
  description text,
  size_limit int,
  is_limited boolean,
  status text CHECK (status = 'open' OR status = 'closed'),
  FOREIGN KEY (user_email) REFERENCES users,
  PRIMARY KEY(group_id)
  );
  
create table courses(
  course_title text,
  course_id int,
  term text,
  department text,
  PRIMARY KEY(course_id)
  );

/* participation constraint */
create table has_sections(
  call_number int,
  professor text,
  course_id int,
  PRIMARY KEY (call_number),
  FOREIGN KEY (course_id) REFERENCES courses
    ON DELETE NO ACTION
  );

/* relations */
create table requests_join(
  user_email text,
  group_id int,
  message text,
  PRIMARY KEY (user_email, group_id),
  FOREIGN KEY(user_email) REFERENCES users,
  FOREIGN KEY(group_id) REFERENCES groups
  );
  
 create table containing(
   call_number int,
   group_id int, 
   PRIMARY KEY(call_number, group_id),
   FOREIGN KEY(call_number) REFERENCES has_sections,
   FOREIGN KEY(group_id) REFERENCES groups
   );
   
create table belongs_to(
  user_email text,
  group_id int,
  PRIMARY KEY(user_email, group_id),
  FOREIGN KEY(user_email) REFERENCES users,
  FOREIGN KEY(group_id) REFERENCES groups
  );
  
/* weak entities */
create table board_posted(
  post_id int,
  group_id int,
  date_time timestamp,
  message text,
  user_email text NOT NULL,
  PRIMARY KEY(post_id, user_email),
  FOREIGN KEY(group_id) REFERENCES groups,
  FOREIGN KEY(user_email) REFERENCES users
    ON DELETE CASCADE
  );
