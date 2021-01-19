from typing import Dict
from interceptors.generic import Interceptor, ProfilingInterceptor, LiteralInterceptor


def profile(interceptors: Dict[str, Interceptor]):
	return {k: ProfilingInterceptor(interceptor, threshold=100) for k, interceptor in interceptors.items()}


def create_modify_specific_fields(interceptors_by_instance: Dict[str, Interceptor], interceptors_by_name: Dict[str, Interceptor], ):
	def modify_specific_fields(fields):
		def modify_field(field):
			return interceptors_by_instance.get(field.get('instance'), LiteralInterceptor()).intercept(
				interceptors_by_name.get(field.get('name'), LiteralInterceptor()).intercept(
					field
				)
			)

		return list(map(modify_field, fields))
		
	return modify_specific_fields


def identity(x): return x
