#!/usr/bin/env python3
import fcntl
from argparse import ArgumentParser
from subprocess import Popen, PIPE
import json
import sys
from qubesadmin import Qubes
from typing import Dict
from interceptors import *
import signal		
import os
from util import profile, create_modify_specific_fields, identity


def look_for_next_array(inp):
	# fcntl seems to have no effect on Process's stdout
	orig_fl = fcntl.fcntl(inp, fcntl.F_GETFL)
	try:
		fcntl.fcntl(inp, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
		c = None
		while c != b'[':
			s = inp.peek(1)
			if len(s) == 0:
				return False
			c = bytes([s[0]])
			if c not in [b' ', b'\t', b'\r', b'\n', b'[']:
				raise Exception("Unexpected data starting with " + str(c) + ": " + str(s))
			if c != b'[':
				inp.read(1)  # Move to the next byte
		# We have found the '['
		print("next: " + str(s))
		return True
	finally:
		fcntl.fcntl(inp, fcntl.F_SETFL, orig_fl)


def intercept_i3status(proc, restarted: bool, modify):
	should_restart = [False]
	def restart(x, y):
		should_restart[0] = True

	signal.signal(signal.SIGUSR1, restart)
	for i in [1, 2]:
		inp = proc.stdout.readline()
		if not restarted:
			sys.stdout.buffer.write(inp)
	sys.stdout.buffer.flush()
	while True:
		inp = json.loads(proc.stdout.readline().decode("UTF-8"))
		sys.stdout.buffer.write(json.dumps(modify(inp)).encode("UTF-8"))
		sys.stdout.buffer.write(b'\n')
		sys.stdout.buffer.flush()
		consume_comma(proc.stdout)
		sys.stdout.buffer.write(b',')
		if should_restart[0]:
			sys.stdout.buffer.write(b'[{"full_text": "Restarting", "color": "#ff0000"}],')
			sys.stdout.buffer.flush()
			os.execle(sys.executable, sys.executable, *sys.argv, {**os.environ, 'RESTARTED': '1'})
		#has_next = look_for_next_array(proc.stdout)
		#if has_next:
		#	print('HAS NEXT!!!')


def consume_comma(stream):
	c = None
	while c != b',':
		c = stream.read(1)
		if c not in [b' ', b'\t', b'\r', b'\n', b',']:
			raise Exception('Unexpected char: '+str(c))


def main():
	parser = ArgumentParser()
	parser.add_argument('--profile-interceptors', action='store_true', default=False)
	args = parser.parse_args()
	profile_if_requested = profile if args.profile_interceptors else identity

	with Popen(["i3status", "-c", os.path.join(os.path.dirname(sys.argv[0]), "i3status.conf")], stdout=PIPE) as proc:
		qubes = Qubes()
		restarted = os.environ.get('RESTARTED') == '1'
		intercept_i3status(proc, restarted, create_modify_specific_fields(interceptors=profile_if_requested({
			'holder_disk_info': DiskInterceptor(qubes),#LatencyInterceptor(100, 5000, 
			'holder_running_qubes': RunningQubesInterceptor(qubes),
		})))


main()
