#from cryptography.fernet import Fernet
#key = Fernet.generate_key()
#print(key)

import os
import hashlib

#Would replace the database array of dictionaries with the actual database
database = []

def create_user(username: str, password: str):
	salt =  os.urandom(32)
	key = hashlib.pbkdf2_hmac(
		'sha256', # The hash digest algorithm for HMAC
		password.encode('utf-8'), # Convert the password to bytes
		salt, # Provide the salt
		100000, # It is recommended to use at least 100,000 iterations of SHA-256 
		dklen=128 # Get a 128 byte key
	)
	storage = salt+key
	object = {
		'username':username,
		'password':storage
	}
	database.append(object)
	print('New user created')

def confirm_password(username:str, password_to_check: str):
	result = list(filter(lambda person: person['username'] == username, database))[0]
	storage = result['password']
	print(password_to_check)

	salt_from_storage = storage[:32] # 32 is the length of the salt
	key_from_storage = storage[32:]
	new_key = hashlib.pbkdf2_hmac(
		'sha256',
		password_to_check.encode('utf-8'), # Convert the password to bytes
		salt_from_storage, 
		100000,
		dklen=128
	)

	if new_key == key_from_storage:
		print('Password is correct')
	else:
		print('Password is incorrect')


create_user('bob2', '2password')
create_user('bob3', '3password')
create_user('bob4', '4password')
#result = list(filter(lambda person: person['username'] == 'bob2', database))[0]
#print(result['password'])
confirm_password('bob2', '2password')
confirm_password('bob2', '2p3assword')
