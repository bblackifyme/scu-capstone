"Simple Persistent datatype for SCU Final 'Code db' requirment"
import json
import random

class CodeDB(dict):
	"""A simple persistent datatype for Capstone code system.

	This DB writes a dictionary to a JSON file on update & delete.

	All usage and calculates are done in memory, however writing is syncronous.
	Could be optimized by asyncronously writing to disk with a que for ordering.
	"""

	def __init__(self, file=None):
		"""Initializer, must be either no initial params or the file input.

		If a file is presented that path is used for the db location.

		If no file is present the path is set to /temp/codedb.json
		"""
		self.file = 'codedb2.json'
		if file:
			try:
				self.file = file
				with open(file, 'r') as f:
					previous_db = json.load(f)
				dict.__init__(self, previous_db)
				return None

			except IOError:
				self.file = file
		with open(self.file, 'w+') as f:
			json.dump({}, f)

	def __delitem__(self, item):
		"delete from json file on delete"
		dict.__delitem__(self, item)
		with open(self.file, 'w') as f:
			json.dump(self, f)

	def update(self, new_dict):
		"save to json file on update"

		# Update DB
		dict.update(self, new_dict)

		with open(self.file, 'w') as f:
			json.dump(self, f)

	def _get_db_raw(self):
		with open(self.file, 'r') as f:
			db = json.load(f)
			return db


class CodeSystem(CodeDB):
	"""Class to be used to check & validate codes against limits.

	Leverages the CodeDB class to handle persistence and writing the system state to disk.
	"""
	def add_code(self, limit=1, code=None):
		"""Generate a new code in the system.

		Default code limit is 1. Allows for providing a code.
		"""
		if code:
			pass
		else:
			code = random.randint(1,100001)

		self.update({code: {"limit":limit, 'valid': True, 'uses': 0, 'users': []}})
		return code

	def check_code_validity(self, code, user):
		if code in self:
			new_record = self.__getitem__(code)
			print self[code]['valid']
			if self[code]['valid'] is True:
				self[code]['uses'] += 1
				self[code]['users'].append(user)
				if self[code]['uses'] >= self[code]['limit']:
					self[code]['valid'] = False
				self.update({code:new_record})
				self.update({user:True})
				return True
		return False

	def get_code_users(self, code):
		return self[code]['users']


######################################################################
################ ******* UNIT TESTS ******** #########################
######################################################################
if __name__ == "__main__":
	# Begin UNITTESTS

	# Create a new DB object
	db = CodeDB()

	# Validate dict inheritance
	assert 'update' in dir(db)

	# Validate update works
	db.update({"new":"stuff"})
	assert 'new' in db
	assert type(db) is CodeDB

	db.update({"new2":"stuff"})
	assert 'new' in db
	assert 'new2' in db

	# Validate update is written to db file
	with open(db.file, 'r') as f:
			live = json.load(f)
			assert type(live) is dict
			assert 'new' in live
			assert 'new2' in live

	# Validate loading a db given a file path
	del db

	# Create teh new db witha. path
	db = CodeDB(file=db.file)

	# Assert the previous data is present
	assert 'new' in db
	assert 'new2' in db

	# Valdiate that deletes are also removed from db
	del db['new']
	with open(CodeDB.file, 'r') as f:
			live = json.load(f)
			assert 'new' not in live

	# Validate raw db getter
	assert 'new2' in db._get_db_raw()

	# Create a code system
	cs = CodeSystem()

	# Make a new Code
	code = cs.add_code(limit=10)
	# Make sure its in system
	assert code in cs
	assert str(code) in cs._get_db_raw()

	# Make a new code
	code2 = cs.add_code(limit=10)
	assert code in cs

	# Specifiy a code
	code3 = cs.add_code(limit=10, code="abc")
	assert "abc" == code3

	# Make sure its different
	assert code != code2

	# Confirm code metadata
	assert cs[code]['valid'] == True
	assert cs[code]['uses'] == 0

	# check that code is valid
	assert cs.check_code_validity(code, 'dummy') == True

	# use code past limit
	for times in range(0,12):
		cs.check_code_validity(code, 'dummy')

	# Confirm limit is passed and code is invalid
	assert cs.check_code_validity(code, 'dummy') == False

	# Test api to get users for a given code
	assert cs.get_code_users(code2) == []
	cs.check_code_validity(code2, 'test')
	assert cs.get_code_users(code2) == ['test']
	assert cs.get_code_users(code2) == cs._get_db_raw()[str(code2)]['users']
