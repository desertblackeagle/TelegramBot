# -*- coding: utf-8 -*-
import sys
import time
import telepot
import urllib3
import json
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

TOKEN = sys.argv[1] 
MAINUSERCHATID = sys.argv[2]
LOCATIONINIT = sys.argv[3] 
TARGETSITE = sys.argv[4] 

#logging init
logHandler = TimedRotatingFileHandler( "./log/log" ,"H" ,1 ,1000)
logFormatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s') 
logHandler.setFormatter( logFormatter )
log = logging.getLogger(name=None)
log.addHandler(logHandler)
log.setLevel( logging.INFO )
log.info("start to logging")


pokemonTargets = []
users = []
usersProfile = dict()
appearTmp = []
securJson = True
targetlocation = LOCATIONINIT
pokemonNumbers = 0
bot = telepot.Bot(TOKEN)
http = urllib3.PoolManager()
r = None

def loadConfig():
	log.info("load config start")
	global pokemonTargets
	global users
	goodJSON = True
	file = open('config.txt', 'r')
	content = file.read()
	try:
		j = json.loads(content)
	except ValueError, e:
		goodJSON = False
		print "load json error\nfile content : "
		print content
	if goodJSON == True:
		pokemonTargets = j['PokemonTargets']
		users = j['Users']
	log.info("PokemonTargets : " + str(pokemonTargets))
	log.info("users : " + str(users))
	log.info("load config end")

def locationChange(msg):
	print msg['location']['latitude']
	print msg['location']['longitude']
	v2 =  float(msg['location']['latitude']+0.006)
	v3 =  float(msg['location']['longitude']+0.01)
	v4 =  float(msg['location']['latitude']-0.006)
	v5 = float(msg['location']['longitude']-0.01)
	print str(v2) + "," + str(v3)
	print str(v4) + "," + str(v5)
	global targetlocation
	targetlocation = "http://"+TARGETSITE+"/raw_data?pokemon=true&pokestops=false&gyms=false&scanned=true&spawnpoints=true&swLat="+str(v4)+"&swLng="+str(v5)+"&neLat="+str(v2)+"&neLng="+str(v3)+"&_=1471877684506"
	print targetlocation
	postlocation = "http://"+TARGETSITE+"/next_loc?lat="+str(msg['location']['latitude'])+"&lon="+str(msg['location']['longitude'])
	r = http.request('POST', postlocation)

def messageHandle(msg):
	if msg['text'] == "pokemoner":
		if chat_id not in users:
			users.append(chat_id)
			bot.sendMessage(MAINUSERCHATID, str(msg['from']) + str(chat_id))
		elif msg['text'] == "users":
			bot.sendMessage(MAINUSERCHATID, users)
		elif msg['text'] == "numbers of pokemon":
			bot.sendMessage(chat_id, pokemonNumbers)
		else :
			bot.sendMessage(chat_id, msg['text'] + " command not find")

def handle(msg):
	content_type, chat_type, chat_id = telepot.glance(msg)
	print(content_type, chat_type, chat_id)
	print msg['from']
	if content_type == 'text':
		messageHandle(msg)
	elif content_type == 'location':
		locationChange(msg)

def pokemonTargetInterest(target):
	return target in pokemonTargets

def newPokemonFind(j):
	print j['pokemons'][i]['pokemon_name'],
	print j['pokemons'][i]['pokemon_id'],
	print " " + str(time.ctime(float(str(j['pokemons'][i]['disappear_time'])[:-3]))) + u" 消失 : 剩餘:",
	print (float(str(j['pokemons'][i]['disappear_time'])[:-3]) - float(time.time()))
	if pokemonTargetInterest(int(j['pokemons'][i]['pokemon_id'])):
		sendmsg = j['pokemons'][i]['pokemon_name'] + " " + str(float(str(j['pokemons'][i]['disappear_time'])[:-3]) - float(time.time()))
		print sendmsg
		for user in users:
			bot.sendMessage(user, sendmsg)
			bot.sendLocation(user, j['pokemons'][i]['latitude'], j['pokemons'][i]['longitude'])	

loadConfig()
bot.message_loop(handle)
print ('Listening ...')

# Keep the program running.
while 1:
	securJson = True
	goodResponse = True
	time.sleep(5)
	try:
		r = http.request('GET', targetlocation)
	except :
		print ("GET request error")
		print "Unexpected error:", sys.exc_info()[0]
		log.info("Unexpected error:" + sys.exc_info()[0])
	
	print "Response Status : "+str(r.status)
	if int(r.status) != 200:
		goodResponse = False
	msg = r.data
	try:
		j = json.loads(msg)
	except ValueError, e:
		print "data format not json"
		securJson = False

	try:
		if securJson == True and goodResponse == True:
			print "Numbers of Pokemon : " + str(len(j['pokemons']))
			pokemonNumbers = len(j['pokemons'])
			for i in range(0,len(j['pokemons'])):
				try:
					if j['pokemons'][i] not in appearTmp:
						appearTmp.append(j['pokemons'][i])
						log.info(json.dumps(j['pokemons'][i], encoding="UTF-8", ensure_ascii=False))
						newPokemonFind(j)
				except KeyError, e:
					print "key error"
					print j['pokemons'][i]
					log.info(str("key error exception ") + str(json.dumps(j['pokemons'][i], encoding="UTF-8", ensure_ascii=False)))
	except:
		bot.sendMessage(MAINUSERCHATID, u"炸掉了")
		print "Unexpected error:", sys.exc_info()[0]
		log.info("Unexpected error:" + sys.exc_info()[0])
	r.close()
