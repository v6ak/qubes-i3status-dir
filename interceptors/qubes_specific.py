from interceptors.generic import Interceptor
import subprocess
from math import floor, log10, log2
from typing import Optional
from qubesadmin import Qubes
from qubesadmin.storage import Pool


def format_space_original(num: float) -> str:
	if num == 0:
		return "0 Bytes"
	elif num < 0:
		raise Error("Unexpected argument: " + str(num))
	else:
		order = log10(num)
		if order <= 4.0:
			return str(floor(num)) + " Bytes"
		elif order <= 7.0:
			return str(floor(num / 1024)) + "K"
		elif order <= 10.0:
			return str(floor(num / 1048576)) + "M"
		elif order <= 13.0:
			return str(floor(num / 1073741824)) + "G"
		else:
			return str(floor(num / 1099511627776)) + "T"


def format_space_v6(num: float) -> str:
	if num == 0:
		return "0B"
	elif num < 0:
		raise Error("Unexpected argument: " + str(num))
	else:
		order = log2(num)
		if order <= 10.0:
			return str(floor(num)) + "B"
		elif order <= 20.0:
			return str(floor(num / 1024)) + "K"
		elif order <= 30.0:
			return str(floor(num / 1048576)) + "M"
		elif order <= 40.0:
			return str(floor(num / 1073741824)) + "G"
		else:
			return str(floor(num / 1099511627776)) + "T"


format_space = format_space_original


class DiskInterceptor(Interceptor):
	#_qubes: Qubes
	#_default_pool_name: Optional[str]
	#_pool: Optional[Pool]
	
	def __init__(self, qubes: Qubes):
		self._qubes = qubes
		self._default_pool_name = None
		self._pool = None
		
	def _update_pool(self):
		if self._qubes.default_pool != self._default_pool_name:
			self._default_pool_name = self._qubes.default_pool
			self._pool = self._qubes.pools[self._default_pool_name]

	def intercept(self, field: dict) -> dict:
		self._update_pool()
		size = int(self._pool.config['size'])
		usage = int(self._pool.config['usage'])
		free = size - usage
		return {'name': 'disk', 'full_text': format_space(free)}


class RunningQubesInterceptor(Interceptor):
	#_qubes: Qubes
	
	def __init__(self, qubes: Qubes):
		self._qubes = qubes

	def intercept(self, field: dict) -> dict:
		running_xen_domains = list(filter(
			lambda s: s!="",
			map(
				lambda s: s.split(b' ', 2)[0].decode('ascii'),
				subprocess.check_output(["xl", "list"]).split(b"\n")[2:]
			)
		))

		# Filter stubdoms. We cannot filter just based on “-dm” suffix, as it can be an ordinary domain!
		running_qubes = list(filter(
			lambda vm_name: vm_name in self._qubes.domains,
			running_xen_domains
		))


		return {'name': 'qubes', 'full_text': str(len(running_qubes)) + " Qubes"}
