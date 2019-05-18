#!/usr/bin/env python3.6

#linux urllib install: sudo apt install python-urllib3 python-requests
# sudo pip3.6 install fbchat


from fbchat import Client
from fbchat.models import *
import getpass
import os
#from urllib3.request import urlretrieve
import requests
from urllib3.util import parse_url
import re
import sys

import argparse

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import time

STEPS = 30



# Instantiate the parser
parser = argparse.ArgumentParser(description='Facebook images downloader')

parser.add_argument('--email', type=str, help='User email', required=True)

parser.add_argument('--chat', type=str, help='Name of conversation', required=True)

parser.add_argument('--password', type=str, help='User password, note that this method is not secure!')
# Required positional argument
parser.add_argument('--last', type=int, metavar='NUM', help='Download last [NUM] images')

# Optional positional argument
parser.add_argument('--messages', type=int, metavar='NUM', help='Fecth last [NUM] messages')

# Switch
parser.add_argument('--all', action='store_true', help='Download all images')

parser.add_argument('--onedir', action='store_true', help='Download to only one directory')

args = parser.parse_args()

'''

if len(sys.argv) == 3:
	if sys.argv[1] == "l":
		latest = int(sys.argv[2])
		print("latest ENABLED !!!!")

'''
email = args.email
password = args.password

print("Using email %s" % email)

if password == None:
	password = getpass.getpass()
else:
	print("Using password from command line: %s" % ('*' * len(password)))



client = Client(email, password, user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0')



'''
# Fetches a list of all users you're currently chatting with, as `User` objects
users = client.fetchAllUsers()

print("users' IDs: {}".format(user.uid for user in users))
print("users' names: {}".format(user.name for user in users))

# If we have a user id, we can use `fetchUserInfo` to fetch a `User` object
user = client.fetchUserInfo('<user id>')['<user id>']
# We can also query both mutiple users together, which returns list of `User` objects
users = client.fetchUserInfo('<1st user id>', '<2nd user id>', '<3rd user id>')

print("user's name: {}".format(user.name))
print("users' names: {}".format(users[k].name for k in users))


# `searchForUsers` searches for the user and gives us a list of the results,
# and then we just take the first one, aka. the most likely one:
user = client.searchForUsers('Michal Tancjura')[0]

print('user ID: {}'.format(user.uid))
print("user's name: {}".format(user.name))
print("user's photo: {}".format(user.photo))
print("Is user client's friend: {}".format(user.is_friend))
'''


def create_dir(name_t):
	name = "attachments"
	if not os.path.exists(name):
		os.makedirs(name)

	if not os.path.exists(name + "/" + name_t):
		os.makedirs(name + "/" + name_t)

	return name + "/" + name_t


create_dir("")   #create attachments directory
create_dir("from_you")
create_dir("from_others")

'''
def download_img(dir, url):
	path = parse_url(url).path
	filename = path[path.rfind("/")+1:]
	print(filename)

	#urlretrieve(url, dir + "/" + filename)  

	with open(dir + "/" + filename, 'wb') as handle:
		response = requests.get(url, stream=True)

		if not response.ok:
			print(response)

		for block in response.iter_content(1024):
			if not block:
				break

			handle.write(block)
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


# Fetches a list of the 20 top threads you're currently chatting with
thread_name = args.chat

uid_c = None
threads = client.fetchAllUsers()

for thread in threads:
	#print(thread.name)
	#print(thread.uid)

	if thread.name.startswith(thread_name):
		uid_c = thread.uid
		print("Found thread with name >%s< and uid >%s<" % (thread.name, thread.uid))
		break



if uid_c == None:
	print("Unable to find thread with name >%s<, exiting" % thread_name)
	client.logout()
	exit(5)



# Fetches the next 10 threads
#threads += client.fetchThreadList(limit=10)

#print("Threads: {}".format(threads))

thread_info = client.fetchThreadInfo(uid_c)[uid_c]
thread_info = client.fetchThreadInfo(uid_c)[uid_c]   #twice because of documentation
messages_count = thread_info.message_count
print("Number of messages in the thread: %d" % messages_count)


messages_number = None
attach_number = None

if args.messages != None:
	messages_number = args.messages
else:
	messages_number = messages_count


if args.all:
	attach_number = messages_count   #maximum number of attachments

elif args.last != None:
	attach_number = args.last

else:
	attach_number = 1

print("Fetching %d messages and trying to donwload %d images" % (messages_number, attach_number))

# Gets the last 10 messages sent to the thread
#messages = client.fetchThreadMessages(thread_id=uid_c, limit=messages_number)
# Since the message come in reversed order, reverse them
#messages.reverse()

'''
# Prints the content of all the messages
ll = 0
for message in messages:
	if message.attachments != None and len(message.attachments) > 0: ll += 1

print(ll)
count = 0
'''








attach_count = 0
last_timestamp = None
messages_count = 0
active = True

while messages_count <= messages_number and active == True:
	#nonlocal active, attach_count, last_timestamp, messages_count

	messages = client.fetchThreadMessages(thread_id=uid_c, limit=min(STEPS, messages_number), before=last_timestamp)

	if last_timestamp != None:
		messages.pop(0)

	messages_count += len(messages)
	print("Total number of messages %d" % messages_count)
	if len(messages) == 0:
		print("End of messages")
		active = False
		break

	last_timestamp = messages[-1].timestamp

	for message in messages:
		print("---------")
		#print(message)
		print(">%s<" % message.text)

		'''
		for msg in messages:
			#print(msg)
			if msg == ImageAttachment:
				print("YES")
		try: 
			print(client.fetchImageUrl(message))
		except:
			pass
		'''
		msg_id = re.sub("[^a-zA-Z0-9]","", message.uid)
		

		if message.attachments != None and len(message.attachments) > 0:
			
			if attach_count <= attach_number:
				'''
				name = ""
				if len(message.attachments) > 1:
					name = create_dir(msg_id)

				else:
					name = create_dir("")

				for act in message.attachments:
					print(act)
					uid = act.uid
					url = client.fetchImageUrl(uid)
					print("URL = %s" % url)

					download_img(name, url)
				'''

				for current in message.attachments:
					print(type(current))

					filename = None
					extension = None
					url = None
					timestamp = float(message.timestamp)/1000
					dir = None
					dir_sub = None

					if client.uid == message.author:
						print("Message from this user")
						dir_sub = "from_you"
					else:
						print("Message from other user/users")
						dir_sub = "from_others"

					if len(message.attachments) > 1 and args.onedir == False:
						dir = create_dir(dir_sub + '/' + msg_id)
					else:
						dir = "attachments/" + dir_sub


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



print("Total number of fetched messages %d, downloaded %d files" % (messages_count, attach_count))


client.logout()

	
'''
# If we have a thread id, we can use `fetchThreadInfo` to fetch a `Thread` object
thread = client.fetchThreadInfo('<thread id>')['<thread id>']
print("thread's name: {}".format(thread.name))
print("thread's type: {}".format(thread.type))


# `searchForThreads` searches works like `searchForUsers`, but gives us a list of threads instead
thread = client.searchForThreads('<name of thread>')[0]
print("thread's name: {}".format(thread.name))
print("thread's type: {}".format(thread.type))
'''

# Here should be an example of `getUnread`