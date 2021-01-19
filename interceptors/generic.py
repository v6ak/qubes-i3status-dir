import time
import random
from abc import ABC, abstractmethod
from typing import Optional
import re

class Interceptor(ABC):
	
	@abstractmethod
	def intercept(self, field: dict) -> dict:
		pass

	def then(self, other):
		return ChainedInterceptor(self, other)


class ChainedInterceptor(Interceptor):
	
	def __init__(self, first: Interceptor, second: Interceptor):
		self._first = first
		self._second = second
	
	def intercept(self, field: dict) -> dict:
		self._second.intercept(self._first.intercept(field))


class LiteralInterceptor(Interceptor):
	
	def intercept(self, field: dict) -> dict:
		return field


class ProfilingInterceptor(Interceptor):
	#_interceptor: Interceptor
	#_threshold: Optional[int]
	_violations = 0
	
	def __init__(self, interceptor: Interceptor, threshold: Optional[int]=None):
		self._interceptor = interceptor
		self._threshold = threshold
	
	def intercept(self, field: dict) -> dict:
		t1 = time.perf_counter()
		res = self._interceptor.intercept(field)
		t2 = time.perf_counter()
		diff_s = t2-t1
		diff_ms = diff_s*1000
		if self._threshold is not None and diff_ms > self._threshold:
			self._violations += 1
		time_str = str(round(diff_ms))+"ms"
		violations_str = ", "+str(self._violations) +" times >"+str(self._threshold)+"ms" if self._violations > 0 else ""
		return {
			**res,
			'full_text': res['full_text'] + "(" + time_str + violations_str + ")"
		}


class LatencyInterceptor(Interceptor):
	# _min_latency: int
	# _max_latency: int
	# _interceptor: Interceptor
	
	def __init__(self, min_latency: int, max_latency: int, interceptor: Interceptor):
		self._min_latency = min_latency
		self._max_latency = max_latency
		self._interceptor = interceptor

	def intercept(self, field: dict) -> dict:
		time.sleep(random.randrange(self._min_latency, self._max_latency)/1000.0)
		return self._interceptor.intercept(field)


class TimedCachingInterceptor(Interceptor):
	# _period: int
	# _counter: int
	# _interceptor: Interceptor
	# _value: dict
	
	def __init__(self, period: int, interceptor: Interceptor):
		self._period = period
		self._counter = 0
		self._interceptor = interceptor

	def intercept(self, field: dict) -> dict:
		if self._counter == 0:
			self._value = self._interceptor.intercept(field)
		self._counter = (self._counter + 1) % self._period
		return self._value


class AcOnlineInterceptor(Interceptor):
	# _ac_suffix: str
	
	def __init__(self, ac_suffix: str = " AC"):
		self._ac_suffix = ac_suffix
		
	def _is_ac_powered(self):
		with open("/sys/class/power_supply/AC/online", "rb") as f:
			return f.read().strip() == b'1'
	
	def intercept(self, field: dict) -> dict:
		return {**field, 'full_text': field['full_text'] + (self._ac_suffix if self._is_ac_powered() else "")}



BATTERY_PERCENTAGE_PATTERN = re.compile('([0-9]+)%')

#class ColorfurBatteryPercentageInterceptor(Interceptor):
#
#	def intercept(self, field: dict) -> dict:
#		percentage = int(BATTERY_PERCENTAGE_PATTERN.search(field['full_text']).group(1))


class BatteryInterceptor(Interceptor):
	# _ac_suffix: str
	
	def __init__(self, ac_suffix: str = " AC"):
		self._ac_suffix = ac_suffix
		
	def _is_ac_powered(self):
		with open("/sys/class/power_supply/AC/online", "rb") as f:
			return f.read().strip() == b'1'
	
	def intercept(self, field: dict) -> dict:
		ac = self._is_ac_powered()
		percentage = int(BATTERY_PERCENTAGE_PATTERN.search(field['full_text']).group(1))
		color = None
		if not ac:
			if percentage < 25:
				color = '#ff0000'
			elif percentage < 50:
				color = '#ffff00'

		return {
			**field,
			'full_text':field['full_text'] + (self._ac_suffix if self._is_ac_powered() else ""),
			'color': color
		}
