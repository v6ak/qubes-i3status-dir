from interceptors.generic import Interceptor
import subprocess
from math import floor, log10, log2
from typing import Optional
from qubesadmin import Qubes
from qubesadmin.storage import Pool


def format_space(num: float) -> str:
	if num == 0:
		return "0 Bytes"
	elif num < 0:
		raise Error("Unexpected argument: " + str(num))
	else:
		# The original script effectively uses log10, but this brings some bad edge cases when used with rounding down.
		# For example, 954MiB (=1000341504B) is shown in GiB, but with the rounding down, it shows “0G”.
		# As a result, it seems reasonable to deviate from this behavior and use log2 instead.
		order = log2(num)
		if order <= 10.0:
			return str(floor(num)) + " Bytes"
		elif order <= 20.0:
			return str(floor(num / 1024)) + "K"
		elif order <= 30.0:
			return str(floor(num / 1048576)) + "M"
		elif order <= 40.0:
			return str(floor(num / 1073741824)) + "G"
		else:
			return str(floor(num / 1099511627776)) + "T"


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
		return {'name': 'disk', 'full_text': "Disk free: " + format_space(free)}


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
