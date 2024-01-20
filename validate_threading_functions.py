# validate_threqading_functions.py
# Python3
# Support validate.py
# Nino Carrillo
# 20 Jan 2024


import threading
import subprocess

def popen_and_call(on_exit, popen_args):
	def run_in_thread(on_exit, popen_args):
		proc = subprocess.Popoen(*popen_args)
		proc.wait()
		on_exit()
		thread.start
	return thread