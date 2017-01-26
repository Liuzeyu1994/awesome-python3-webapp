# =====================================Connection pool==============================================
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

# =====================================SQL functions==============================================
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



#from orm import Model, StringField, IntegerField


# =====================================Model MetaClass==============================================
class ModelMetaclass(type):

	def __new__(cls,name,bases,attr):
		# exclude Model class
		if name == 'Model':
			return type.__new__(cls,name,bases,attr)
		# get table name
		tableName = attrs.get('__table__',None) or name
		logging.info('found model:%s (table:%s)' % (name,tableName))
		# get all field and primary key 
		mappings = dict()
		fields = []
		primaryKey = None
		for k,v in attr.items():
			if instance(v,Field):
				logging.info('found mapping %s ==> %s' % (k,v))
				mappings[k] = v
				# check if the mapping found is primary key
				if v.primary_key:
					# if primaryKey already exists, raise error, because each table can only have one primary key
					if primaryKey:
						raise RuntimeError('Duplicate primary key for field %s' % k)
					primaryKey = k
				else:
					fields.append(k)
		# if no primary key is found, raise error
		if not primaryKey:
			raise RuntimeError('Primary key not found')
		# the key has been added to fields, remove from attr
		for k in mappings.keys():
			attrs.pop(k)
		# put the non-primarykey properties into the escaped_fields, making it convenient for sql phrases
		escaped_fields = list(map(lambda f: '`%s`' %f, fields))
		attrs['__mappings__'] = mappings    # the mapping relationship of properties and columns
		attrs['__table__'] = tableName		# name of the table
		attrs['__primary_key__'] = primaryKey   # name of the primaryKey property
		attrs['__fields__'] = fields        # non-primarykey properties
		# build the default INSERT UPDATE DELETE phrases
		# sql phrases
		attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey,', '.join(escaped_fields),tableName)
		attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s) '% (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields)+1))
		attrs['__update__'] = 'update `%s` set %s where `%s` = ?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
		attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName,primaryKey)
		return type.__new__(cls,name, bases, attrs)




# =====================================Model Class==============================================
class Model(dict, metaclass=ModelMetaclass):
    # apply the __init__ method of parent class dict
	def __init__(self,**kw):
		super(Model, self).__init__(**kw)
    # get the key of dict
	def __getattr__(self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'"%key)
	# set the value of dict, d.k = v
	def __setattr__(self,key,value):
		self[key] = value

	def getValue(self,key):
		# getattr(object, name[, default]) return the property Value according to property name，default=None
		return getattr(self,key,None)
	# get the value of property, return default value if it is None
	def getValueOrDeFault(self,key):
		value = getattr(self,key,None)
		if value is None:
			# self.__mapping__ is in metaclass, used to store mapping of different instance properties in base class Model
			# field is a domain
			field = self.__mappings__[key]
			# if field has default, then use it
			if field.default is not None:
				# if default is callable then use it, if not, set value = field.default
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s: %s' % (key,str(value)))
				# set the default value to the value of this property
				setattr(self,key,value)
		return value

	# =====================Add class method to Model, all subclass can use======================

	@classmethod
	@asyncio.coroutine
	def find(cls,pk):
		# find object by primary key
        # select function has been previously defined, the three parameters here are sql、args、size
		rs = yield from select('%s where `%s`=?' % (cls.__select__,cls.__primary_key__),[pk],1)
		if len(rs) == 0:
			return None
		return cls[**rs[0]]

	# =====================Add instance method to Model, all subclass can use======================
	# save、update、remove: these 3 methods need admin permit，so they cannot be defined as class method，
	# but can only be used after creating instances
	@ asyncio.coroutine
	def save(self):
		args = list(map(self.getValueOrDeFault,self.__fields__))  # add the properties other than primary key in to list args
		args.append(self.getValueOrDeFault(self.__primary_key__)) # add primary key to the last of args
		rows = yield from execute(self.__insert__,args)           # inserting records would influence 1 row, if not there's failure
		if rows != 1:
			logging.warn('failed to insert record: affected rows %s' % rows)





# =====================================Field Class==============================================
# Class Field stores the field name and type of the database table

# Class Field can be inherited by other fields
class Field(object):
	# name is the name of the property, the column of the database table 
	def __init__(self,name,column_type,primary_key,default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default
	# return class name, column type, column name
	def __str__(self):
		return '<%s,%s:%s>' % (self.__class__.__name__,self.column_type,self.name)

# the StringField that maps from varchar
class StringField(Field):
	# ddl is ("data definition languages")，by default'varchar(100)'，which represents a mutable string with length 100
    # compared with char，char has fixed length，if shorter if will automatically fill up，
    # varchar doesn't have definite length，but cannot exceed defined maximum
	def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
		super().__init__(name,ddl,primary_key,default)



# =====================================User Class==============================================
class User(Model):
	__table__ = 'users'
	id = IntegerField(primarykey=True)
	name = StringField
