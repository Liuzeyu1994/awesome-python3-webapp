## create connection pool
@asyncio.coroutine
def create_pool(loop,**kw):
	logging.info('create database connection pool')
	global __pool
	__pool = yield from aiomysql.create_pool(
		# the following parameters are obtaianed from keyword parameter kw
		host = kw.get('host','local host'), #database server, by defaullt 'local host'
        port = kw.get('port',3306),	# port of sql, by default 3306
        user = kw['user'],	# log in user name, in kw
        password = kw['password'],  # log in password
        db = kw['db'],	# current database name
        charset = kw.get('charset','utf8'),	# set character encoding as UTF8
        autocommit = kw.get('autocommit',Ture),	# set automatic commit as True
        maxsize = kw.get('maxsize',10),	# set maximum number of connections
        minsize = kw.get('minsize',1),	# to garantee that there is at least one connection at any time
        loop = loop	# for coroutines
    )

## SQL functions
# the parameter sql is the sql phrases, args is what you are looking for, 
# size is the maximum number of queries, by default would return all query results
@asyncio.coroutine
def select(sql,args, size=None):
	log(sql,args)
	# use the connection pool created by the create_pool() function
	global __pool
	# get a database connection from the connection pool
	# the with phrase is for closing conn and deal with abnormal conditions
	with (yield from __pool) as conn:
		# create cursor object to execute sql phrases
		cur = yield from conn.cursor(aiomysql.DictCursor)
		# set execution phrases, in Python the placeholder is '%s'
		# while in SQL the placeholder is '?', so we do the replacemet
		# args is the argument of SQL phrases
		yield from cur.execute(sql.replace('?','%s'),args or ())
		# if the number of queries are assigned, return that number of results
		# else, return all
		if size:
			rs = yield from cur.fetchmany(size)
		else:
			rs = yield from cur.fetchall()
		yield from cur.close()
		logging.info('rows returned: %s' %len(rs))
		# return the set of results
		return rs

# define the execute function for INSERT, UPDATE and DELETE
@asyncio.coroutine
def execute(sql,args):
	# the execute() function only returns the number of results
	log(sql)
	with (yield from __pool) as conn:
		try:
			cur = yield from conn.cursor()
			yield from cur.execute(sql.replace('?','%s'),args)
			affected = cur.rowcount
			yield from cur.close()
		except BaseException as e:
			raise
		return affected



from orm import Model, StringField, IntegerField

class User(Model):
	__table__ = 'users'
	id = IntegerField(primarykey=True)
	name = StringField

class Model(dict, metaclass=ModelMetaclass):

	def __init__(self,**kw):
		super(Model, self).__init__(**kw)

	def __getattr__(self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'"%key)
	def __setattr__(self,key,value):
		self[key] = value

	def getValue(self,key):
		return getattr(self,key,None)

	def getValueOrDeFault(self,key):
		value = getattr(self,key,None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s: %s' % (key,str(value)))
				setattr(self,key,value)
		return value
		