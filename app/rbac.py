from code_db import CodeDB

class RbacSystem(CodeDB):
	"RBAC control system"

	def add_role(self, role, sub_roles=None):
		"add a new role into the system"
		if "roles" not in self:
			self.update({"roles":{}})

		self['roles'].update({role:{'sub_roles':[]}})
		if sub_roles is not None:
			assert type(sub_roles) == list
			for rol in sub_roles:
				assert role in self['roles']
			self['roles'][role]['sub_roles'].extend(sub_roles)

	def add_user(self, user, role):
		"add a new user with a specified role"
		assert role in self['roles']
		if "users" not in self:
			self.update({"users":{}})

		self['users'].update({user:[role]})

	def grant_user(self, user, role):
		"grant a user access to a role"
		self['users'][user].append(role)

	def check_access(self, user, role):
		"check if a user is granted a cerain role"
		roles = self['users'][user]
		extended_roles = []
		extended_roles.extend(roles)
		for granted_role in roles:
			sub_roles = extract_roles(granted_role, self)
			extended_roles.extend(sub_roles)
		return role in extended_roles


def _recursive(role, sub_roles, accum, db):
	if sub_roles == []:
		print "done"
		accum.append(role)
		return accum
	accum.append(role)
	for rle in sub_roles['sub_roles']:
		_recursive(rle, db['roles'][rle], accum, db)
	return accum

def extract_roles(role, db):
		"This is needed due tro python colletions in func definition."
		db = dict(db)
		return _recursive(role, db['roles'][role], [], db)


if __name__ == "__main__":
	rb = RbacSystem()
	rb.add_role("GSA")
	assert "GSA" in rb['roles']
	assert rb['roles']['GSA']['sub_roles'] == []
	rb.add_role("admin", sub_roles=["GSA"])
	rb.add_role("super_admin", sub_roles=["admin"])
	assert rb['roles']['super_admin']['sub_roles'] == ["admin"]
	rb.add_user("bblack@scu.edu", "GSA")
	assert "bblack@scu.edu" in rb['users']
	assert rb.check_access("bblack@scu.edu", "super_admin") is False
	assert rb.check_access("bblack@scu.edu", "admin") is False
	assert rb.check_access("bblack@scu.edu", "GSA")
	rb.grant_user("bblack@scu.edu", "super_admin")
	assert rb.check_access("bblack@scu.edu", "admin")
	assert ['super_admin', 'admin', 'GSA'] == extract_roles('super_admin', rb)
	assert ['admin', 'GSA'] == extract_roles('admin', rb)
	assert ['GSA'] == extract_roles('GSA', rb)







