#!/usr/bin/env python3.6

#sudo pip3.6 install fbchat


from fbchat import Client
from fbchat.models import *
import getpass

import argparse

from datetime import datetime


STEPS = 30   #how many messages will be downloaded



# Instantiate the parser
parser = argparse.ArgumentParser(description='Facebook chat messages downloader')

parser.add_argument('--email', type=str, help='User email', required=True)
parser.add_argument('--chat', type=str, help='Name of conversation', required=True)
parser.add_argument('--password', type=str, help='User password, note that this method is not secure!')
parser.add_argument('--last', type=int, metavar='NUM', help='Print last [NUM] messages instead of all')
parser.add_argument('--file', type=str, help='Write messages to file')
parser.add_argument('--lastfirst', action='store_true', help='Last message will be first')
parser.add_argument('--printmessages', action='store_true', help='Print messages to stdout')

args = parser.parse_args()


email = args.email
password = args.password
thread_name = args.chat

print("Using email %s" % email)

if password == None:
	password = getpass.getpass()
else:
	print("Using password from command line: %s" % ('*' * len(password)))



client = Client(email, password, user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0')





#-----get searched user's thread uid-----
uid_c = None
threads = client.fetchAllUsers()   #get all user's threads

for thread in threads:  #iterate over threads
	#print(thread.name)
	#print(thread.uid)

	if thread.name.startswith(thread_name):   #check if current thread starts with passed chat name
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


messages_number = messages_count
if args.last != None: messages_number = args.last

print("Fetching %d messages" % messages_number)
#-----fetch and set number of attachments and messages-----




last_timestamp = None
messages_count = 0
active = True
messages_list = []

try:
	while messages_count <= messages_number and active == True:
		#nonlocal active, attach_count, last_timestamp, messages_count

		messages = client.fetchThreadMessages(thread_id=uid_c, limit=min(STEPS, messages_number + 1), before=last_timestamp)   #get specific number of messages starting at last timestamp

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
			if client.uid == message.author:
				author = "     You"
			else:
				author = "Not You"

			date = datetime.utcfromtimestamp(int(message.timestamp)/1000).strftime('%H:%M:%S %d.%m.%Y')
			messages_list.append((date, author, message.text))

except KeyboardInterrupt:
	print("Keyboard interrupt, leaving while loop")



if not args.lastfirst:
	messages_list.reverse()


f = None
if args.file != None:
	f = open(args.file, "w")

for date, author, msg in messages_list:
	s = "%s %s: >%s<" % (date, author, msg)

	if args.printmessages: print(s)
	if f != None: f.write(s + '\n')

if f != None: f.close()


print("Total number of fetched messages %d" % messages_count)

client.logout()