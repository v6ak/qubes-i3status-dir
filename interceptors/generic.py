import time
import random
from abc import ABC, abstractmethod
from typing import Optional


class Interceptor(ABC):
	
	@abstractmethod
	def intercept(self, field: dict) -> dict:
		pass


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
		return {
			**field,
			'full_text':
				res['full_text'] +
					"("+str(round(diff_ms))+"ms"+
					(", "+str(self._violations) +" times >"+str(self._threshold)+"ms" if self._violations > 0 else "") +
					")"}


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
