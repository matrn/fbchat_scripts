#!/usr/bin/env python3.6

#linux urllib install: sudo apt install python-requests
#sudo pip3.6 install fbchat


from fbchat import Client
from fbchat.models import *
import getpass
import os
#from urllib3.request import urlretrieve
import requests
import re
import sys

import argparse

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import time

STEPS = 30   #how many messages will be downloaded



# Instantiate the parser
parser = argparse.ArgumentParser(description='Facebook chat attachments downloader')

parser.add_argument('--email', type=str, help='User email', required=True)
parser.add_argument('--chat', type=str, help='Name of conversation', required=True)
parser.add_argument('--exact', action='store_true', help='Exact chat name')
parser.add_argument('--password', type=str, help='User password, note that this method is not secure!')
parser.add_argument('--last', type=int, metavar='NUM', help='Download last [NUM] images')
parser.add_argument('--messages', type=int, metavar='NUM', help='Fecth last [NUM] messages')
parser.add_argument('--all', action='store_true', help='Download all images')
parser.add_argument('--onedir', action='store_true', help='Download to only one directory')
args = parser.parse_args()


email = args.email
password = args.password
thread_name = args.chat

print("Using email %s" % email)

if password == None:
	password = getpass.getpass()
else:
	print("Using password from command line: %s" % ('*' * len(password)))



client = Client(email, password, user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0')



'''
 Function for crreating directory
 Return value:
    name of created directory
'''
def create_dir(name_t):
	name = "attachments"
	if not os.path.exists(name):
		os.makedirs(name)

	if not os.path.exists(name + "/" + name_t):
		os.makedirs(name + "/" + name_t)

	return name + "/" + name_t


create_dir("")   #create attachments directory
create_dir("from_you")   #create directory for attachments from this user
create_dir("from_others")   #create directory for attachments from other users



'''
 Function for downloading file from url and setting correct utime
'''
def download_file(dir, url, timestamp):
	filename = os.path.basename(urlparse.urlparse(url).path)

	#urlretrieve(url, dir + "/" + filename)  
	print("Filename >%s<" % filename)

	path = dir + "/" + filename

	if os.path.isfile(path):
		files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]   #get all files in dir
		p = filename.partition('.')
		result = [i for i in files if i.startswith(p[0])]   #get all similiar files

		filename = "%s(%d).%s" % (p[0], len(result) + 1, p[2]) 
		path = dir + '/' + filename

		print("!Added number to file, filename >%s<" % filename)


	print("Writting to >%s<" % path)


	with open(path, 'wb') as handle:
		response = requests.get(url, stream=True)

		if not response.ok:
			print("RESPONSE NOT OK:")
			print(response)

		for block in response.iter_content(1024):
			if not block:
				break

			handle.write(block)


	print("setting time of file modify")
	os.utime(path, (time.time(), int(timestamp)))





#-----get searched user's thread uid-----
uid_c = None
threads = client.fetchAllUsers()   #get all user's threads

for thread in threads:  #iterate over threads
	#print(thread.name)
	#print(thread.uid)

	if (args.exact == False and thread.name.startswith(thread_name)) or (args.exact == True and thread.name == thread_name):   #check if current thread starts with passed chat name
		uid_c = thread.uid
		print("Found thread with name >%s< and uid >%s<" % (thread.name, thread.uid))
		break


if uid_c == None:
	print("Unable to find thread with name >%s<, exiting" % thread_name)
	client.logout()
	exit(5)
#-----get searched user's thread uid-----


#-----fetch and set number of attachments and messages-----
thread_info = client.fetchThreadInfo(uid_c)[uid_c]
thread_info = client.fetchThreadInfo(uid_c)[uid_c]   #twice because of documentation but idk
messages_count = thread_info.message_count
print("Number of messages in the thread: %d" % messages_count)


messages_number = None
attach_number = None

if args.messages != None:   #set number of messages to fetch
	messages_number = args.messages

else:   #number of messages to fetch is not specified so set to maximum
	messages_number = messages_count


if args.all:   #if all attachments is specified
	attach_number = messages_count   #maximum number of attachments


elif args.last != None:   #if last X attachments is specified
	attach_number = args.last

else:
	attach_number = 1

print("Fetching %d messages and trying to donwload %d images" % (messages_number, attach_number))
#-----fetch and set number of attachments and messages-----




attach_count = 0
last_timestamp = None
messages_count = 0
active = True

try:
	while messages_count <= messages_number and active == True:
		#nonlocal active, attach_count, last_timestamp, messages_count

		messages = client.fetchThreadMessages(thread_id=uid_c, limit=min(STEPS, messages_number), before=last_timestamp)   #get specific number of messages starting at last timestamp

		if last_timestamp != None:   #remove first item because it's message with passed timestamp and we don't want it
			messages.pop(0)

		messages_count += len(messages)
		print("Number of fetched messages %d" % messages_count)

		if len(messages) == 0:
			print("End of messages")
			active = False
			break


		last_timestamp = messages[-1].timestamp   #save new timestamp


		for message in messages:   #iterate over messages
			print("---------")
			#print(message)
			print(">%s<" % message.text)
			#if message.unset: print("Message removed!")


			msg_id = re.sub("[^a-zA-Z0-9]","", message.uid)   #get from message uid only letters and numbers
			

			if message.attachments != None and len(message.attachments) > 0:   #check if message has any attachments
				
				if attach_count <= attach_number:
					for current in message.attachments:   #iterate over attachments
						print(type(current))

						filename = None
						extension = None
						url = None
						timestamp = float(message.timestamp)/1000
						dir = None
						dir_sub = None


						#-----create and chooose correct directory-----
						if client.uid == message.author:
							print("Message from this user")
							dir_sub = "from_you"
						else:
							print("Message from other user/users")
							dir_sub = "from_others"


						if len(message.attachments) > 1 and args.onedir == False:   #if enabled, create directory for more attachments in one message
							dir = create_dir(dir_sub + '/' + msg_id)
						else:
							dir = "attachments/" + dir_sub
						#-----create and chooose correct directory-----


						#-----detect attachment type-----
						if isinstance(current, ImageAttachment):
							print("It's image")
							extension = current.original_extension
							url = client.fetchImageUrl(current.uid)

						if isinstance(current, AudioAttachment):
							print("It's audio")
							filename = current.filename
							extension = filename.split('.')[-1]
							url = current.url

						if isinstance(current, VideoAttachment):
							print("It's video")
							url = current.preview_url

						if isinstance(current, FileAttachment):
							print("It's a file")
							url = current.url
							print(url)
							name = current.name
							#malicious = current.is_malicous
							size = current.size
						#-----detect attachment type-----


						if url != None and timestamp != None:
							attach_count += 1
							print("%d. Downloading >%s< to directory >%s<" % (attach_count, url, dir))
							download_file(dir, url, timestamp)

						else:
							print("Not downloading")

				else:
					print("Downloaded %d attachments" % attach_count)
					active = False
					break
except Exception as e:
	print(e)


client.logout()

print("Total number of fetched messages %d, downloaded %d files" % (messages_count, attach_count))