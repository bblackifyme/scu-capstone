from datetime import datetime
import numpy as np
from collections import Counter

waits = {"a":5*60}

class WaitQue(list):
	"class repersenting a waiting que"

	def __init__(self):
		self.waits = []
		self.seen = None

	def add(self, visitor):
		"append an object returns an estiamted waittime"
		visitor.enter_time = datetime.now()
		list.append(self, visitor)
		que_time = self._get_total_wait()
		if self.seen:
			seen_remaining = self._seen_time_remaining()
			wait = WaitQue._sec_to_min(que_time + seen_remaining)
			visitor.est_wait = wait
		if len(self) == 0:
			wait = WaitQue._sec_to_min(0)
			visitor.est_wait = wait
		wait = WaitQue._sec_to_min(que_time)
		visitor.est_wait = wait
		return wait

	def get_next(self):
		next = self.pop(0)
		next.exit_time = datetime.now()
		wait = float((next.exit_time - next.enter_time).total_seconds())
		self.waits.append(wait)
		self.seen = next
		return next

	def _seen_time_remaining(self):
		"get time remaining for student being seen"
		now = datetime.now()
		time_in = now - self.seen.exit_time
		if time_in.total_seconds() < self._get_reason_wait(self.seen.reason):
			time_remaining = time_in.total_seconds()
			return time_remaining
		else:
			return 0

	def avg_wait(self):
		return np.average(self.waits)

	def get_reasons(self):
		return dict(Counter([student.reason for student in self]))

	@classmethod
	def _get_reason_wait(self, reason):
		waits = {
			"Travel Signature": WaitQue._min_to_sec(5),
			"Status Change" : WaitQue._min_to_sec(15),
			"CPT/OPT Related": WaitQue._min_to_sec(15),
			"OPT Review" : WaitQue._min_to_sec(10),
			"Probation": WaitQue._min_to_sec(10),
			"Reduce Course Load": WaitQue._min_to_sec(1),
			"Other": WaitQue._min_to_sec(5),
		}
		return waits[reason]

	def _get_total_wait(self):
		return sum([WaitQue._get_reason_wait(student.reason) for student in self])
	@classmethod
	def _min_to_sec(self, mini):
		return mini * 60

	@classmethod
	def _sec_to_min(self, sec):
		return sec/60

	def purge(self):
		self.seen = None
		while len(self) != 0:
			for indx, thing in enumerate(self):
				del self[indx]
		


class Visitor(object):

	def __init__(self, name, reason):
		self.name = name
		self.reason = reason


### TEST
if __name__ == "__main__":
	q = WaitQue()
	s = Visitor("a", "Travel Signature")
	s2 = Visitor("b", "Status Change")
	s3 = Visitor("b", "Status Change")
	q.add(s)
	q.add(s2)
	q.add(s3)
	assert s in q
	assert s.enter_time
	import time
	get = q.get_next()
	assert s.exit_time
	assert get is s
	assert q.avg_wait() > 0
	c = q.get_reasons()
	assert c['Status Change'] == 2
	assert q._get_reason_wait("Travel Signature") == 5*60
	s = Visitor("a", "Travel Signature")
	q.add(s)
	s = Visitor("a", "Travel Signature")
	assert q.add(s) > 0
	q._seen_time_remaining() > 0
	q.purge()
	assert q.seen == None
	assert q == []
	assert  q.add(s) == 5


