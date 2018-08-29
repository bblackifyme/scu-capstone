from datetime import datetime
import numpy as np

waits = {"a":5*60}

class WaitQue(list):
	"class repersenting a waiting que"

	def __init__(self):
		self.waits = []

	def append(self, visitor):
		"append an object"
		visitor.enter_time = datetime.now()
		list.append(self, visitor)

	def get_next(self):
		next = self.pop(0)
		next.exit_time = datetime.now()
		wait = float((next.exit_time - next.enter_time).total_seconds())
		self.waits.append(wait)
		return s

	def avg_wait(self):
		return np.average(self.waits)

class Visitor(object):

	def __init__(self, name, reason):
		self.name = name
		self.reason = reason


### TEST

q = WaitQue()
s = Visitor("a", "b")
q.append(s)
assert s in q
assert s.enter_time
get = q.get_next()
assert get is s
assert q.avg_wait() > 0