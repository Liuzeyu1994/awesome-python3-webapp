import time
# uuid is a python library for generating ID
import uuid

from orm import Model, StringField, BooleanField, FloatField, TextField

# generate an id based on time, to be used as primary key
def next_id():
	# time.time() returns the current time with respect to 1970.1.1 00:00:00
	# uuid4 generate from pseudorandom number
	return '%015d%s000' %(int(time.time()*1000),uuid.uuid4().hex)

# a table for user 
class User(Model):
	__table__ = 'users'

	id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
	email = StringField(ddl='varchar(50)')
	passwd = StringField(ddl='varchar(50)')
	admin = BooleanField()		# True means the user is administrator
	name = StringField(ddl='varchar(50)')
	image = StringField(ddl='varchar(500)')		# user image
	# time of creation, by default is the current time
	# date and time is stored as float, not datetime, to avoid time zone transformation
	# to display date and time, just do a transform from float to str
	created_at = FloatField(default=time.time)	

# a table for blog
class Blog(Model):
	__table__ = 'blogs'

	id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
	user_id = StringField(ddl='varchar(50)')	# author's id
	user_name = StringField(ddl='varchar(50)')	# author's name
	user_image = StringField(ddl='varchar(500)')	#the image that author uploads
	name = StringField(ddl='varchar(50)')		# name of the article
	summary = StringField(ddl='varchar(200)')	# summary of the article
	content = TextField()						# content of the article
	created_at = FloatField(default=time.time)

# a table for comments
class Comment(Model):
	__table__ = 'comments'

	id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
	blog_id = StringField(ddl='varchar(50)')	# blog id
	user_id = StringField(ddl='varchar(50)')	# commenter's id 
	user_name = StringField(ddl='varchar(50)')	# commenter's name
	user_image = StringField(ddl='varchar(500)')	# the image that commenter uploads
	content = TextField()
	created_at = FloatField(default=time.time)