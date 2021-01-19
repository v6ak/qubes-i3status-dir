#!/usr/bin/env python3
import asyncio
from argparse import ArgumentParser
from subprocess import PIPE
import json
import sys
from qubesadmin import Qubes
from typing import Dict
from interceptors import *
import signal		
import os
from util import profile, create_modify_specific_fields, identity

# i3status-wrapper.py rewritten to use async I/O in order to handle input skipping


class HeaderHandler():
	_lines_missing=2
	_rest=b''
	
	def __init__(self, parent_handler, header_line_handler):
		self._parent_handler = parent_handler
		self._header_line_handler = header_line_handler
	
	def process_header(self, fd, data):
		lines = (self._rest + data).split(b'\n', self._lines_missing+1)
		self._rest = lines[-1]  # The unterminated line
		for line in lines[0:-1]:  # All lines but the unterminated one
			self._lines_missing = self._lines_missing - 1
			self._header_line_handler(line)
		
		# Check if header is finished
		if self._lines_missing == 0:
			self._parent_handler.pipe_data_received = self._parent_handler._process_status_data
			self._parent_handler.pipe_data_received(fd, self._rest)


class I3SubprocessHandler(asyncio.SubprocessProtocol):
	exited_event = asyncio.Event()
	skipped_lines = 0
	_status_line_event = asyncio.Event()
	_status_line = None
	_rest=b''
	
	def __init__(self, header_line_handler):
		self.pipe_data_received = HeaderHandler(self, header_line_handler).process_header
	
	def process_exited(self):
		self.exited_event.set()
		
	def _process_status_line(self, line):
		# This allows to skip lines when the consumer is not able to handle them
		if self._status_line is not None:
			self.skipped_lines = self.skipped_lines + 1
		self._status_line = line
		self._status_line_event.set()
	
	async def next_status_line(self):
		# TODO: handle exit
		await self._status_line_event.wait()
		l = self._status_line
		self._status_line = None
		self._status_line_event.clear()
		return l

	def _process_status_data(self, fd, data):
		lines = (self._rest + data).split(b'\n')
		self._rest = lines[-1]  # The unterminated line
		for line in lines[0:-1]:  # All lines but the unterminated one
			self._process_status_line(line)		


def create_add_skipped_statuses(protocol: I3SubprocessHandler):
	return \
		lambda f: \
			lambda fields: \
				f(fields) + (
					[{'full_text': 'Skipped statuses: '+str(protocol.skipped_lines)}] if protocol.skipped_lines != 0 else []
				)


async def async_main():
	parser = ArgumentParser()
	parser.add_argument('--profile-interceptors', action='store_true', default=False)
	parser.add_argument('--profile-skipped-statuses', action='store_true', default=False)
	args = parser.parse_args()
	profile_if_requested = profile if args.profile_interceptors else identity
	qubes = Qubes()
	restarted = os.environ.get('RESTARTED') == '1'

	should_restart = [False]
	def restart(x, y):
		should_restart[0] = True

	signal.signal(signal.SIGUSR1, restart)
	
	def header_line_handler(line):
		if not restarted:
			sys.stdout.buffer.write(line)
			sys.stdout.buffer.write(b'\n')
			sys.stdout.buffer.flush()
	
	transport, protocol = await asyncio.get_event_loop().subprocess_exec(lambda: I3SubprocessHandler(header_line_handler), *["i3status", "-c", os.path.join(os.path.dirname(sys.argv[0]), "i3status.conf")], stdout=PIPE)
	
	potentially_add_skipped_statuses = create_add_skipped_statuses(protocol) if args.profile_skipped_statuses else identity
	
	modify = potentially_add_skipped_statuses(create_modify_specific_fields(interceptors=profile_if_requested({
		'holder_disk_info': DiskInterceptor(qubes), #LatencyInterceptor(100, 5000, ),
		'holder_running_qubes': RunningQubesInterceptor(qubes),
	})))
	
	try:
		while True:
			status_line = await protocol.next_status_line()
			inp = json.loads(status_line.strip(b',').decode("UTF-8"))
			sys.stdout.buffer.write(json.dumps(modify(inp)).encode("UTF-8"))
			sys.stdout.buffer.write(b'\n')
			sys.stdout.buffer.flush()
			sys.stdout.buffer.write(b',')
			if should_restart[0]:
				sys.stdout.buffer.write(b'[{"full_text": "Restarting", "color": "#ff0000"}],')
				sys.stdout.buffer.flush()
				os.execle(sys.executable, sys.executable, *sys.argv, {**os.environ, 'RESTARTED': '1'})			
	finally:
		transport.kill()


def on_exception(loop, e):
	print("\n\n\n")
	print(e)
	sys.exit(1)


loop = asyncio.get_event_loop()
loop.add_signal_handler(signal.SIGTERM, loop.stop)
loop.set_exception_handler(on_exception)
loop.run_until_complete(async_main())

