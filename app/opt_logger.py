"Simple logger for OPT/CPT System"
from datetime import datetime

class Logger(object):
	"Simple logger"

	def __init__(self, filename=None):
		if filename:
			self.filename = filename
		else:
			self.filename = "%s_logs.log" % __name__
		with open(self.filename, "a") as f:
			f.write("")

	def info(self, message):
		"Log a informational message"
		with open(self.filename, "a") as f:
			msg = "%s INFO: %s \n" % (datetime.now(), message)
			f.write(msg)

	def raw(self, message):
		"Log a informational message"
		with open(self.filename, "a") as f:
			msg = message
			f.write("\n"+msg)

	def load(self):
		"Read logs into memory"
		with open(self.filename, "r") as f:
			return [log for log in f.readlines()]

	def clear(self):
		"Delete / clear the log file"
		with open(self.filename, "w") as f:
			f.write("")



if __name__ == "__main__":

	l = logger()
	assert l.filename == '__main___logs.log'
	del l

	l = logger(filename='test.log')
	assert l.filename == "test.log"

	l.clear()
	assert len(l.load()) is 0
	l.info("test")
	with open(l.filename, "r") as f:
		for first in f.readlines():
			assert "test" in first
			break

	l.info("test2")
	logs = l.load()
	assert "test" in logs[0]
	assert "test2" in logs[1]