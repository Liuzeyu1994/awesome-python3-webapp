# how to use this test file
# step 1: cd to mysql server bin and run mysql
# step 2: open another window, cd to this foler and run python test.py. 
# Note! this can only be executed once because otherwise user key email would be duplicate
# step 3: check if the table has been created. 
# Attention! the table name is users not user!
'''
import mysql.connector
conn = mysql.connector.connect(user='root', password='password', database='awesome')
cursor = conn.cursor()
cursor.execute('select * from users where name = %s', ('test20',))
values = cursor.fetchall()
values
'''
import orm,asyncio,sys
from models import User, Blog, Comment

async def test(loop):
	await orm.create_pool(loop=loop,user='www-data',password='www-data',db='awesome')

	u = User(name='test20',email='test20@test.com',passwd='test',image='about:blank')

	await u.save()

if __name__ == '__main__':

	loop = asyncio.get_event_loop()
	loop.run_until_complete(asyncio.wait([test( loop )]))
	loop.close()
	if loop.is_closed():
		sys.exit(0)