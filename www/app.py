# the logging module defines several functions and modules for journal processing
# logging module can record errors and continue to execute after recording the errors
import logging; 
# set the level of loggging to INFO
# hierarchy of journal：CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
logging.basicConfig(level=logging.INFO)
# asyncio module for asynchornous IO
import asyncio
# os module for using functions of operating system
import os
# json module for trasforming python objects to json modules
import json
# time module for functions dealing with time
import time
# datetime module dealing with dates and time
from datetime import datetime
# aiohttp is the http framework based on asyncio
from aiohttp import web

'''
from jinja2 import Environment, FileSystemLoader
import orm
from coroweb import add_routes, add_static
'''

def index(request):
	return web.Response(body=b'<h1>Awesome</h1>')

async def init(loop):
	app = web.Application(loop=loop)
	app.router.add_route('GET','/',index)
	srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
	logging.info('server started at http://129.0.0.1:9000...')
	return srv

loop=asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
