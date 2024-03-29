# validate_threading_functions.py
# Python3
# Support validate.py
# Nino Carrillo
# 20 Jan 2024


import threading
import subprocess

def end_do_nothing():
	return

def ClearQueue(q):
	while not q.empty():
		q.get()

# adapted from https://stackoverflow.com/questions/2581817/python-subprocess-callback-when-cmd-exits
def popen_and_call(on_exit, *popen_args):
	"""
	Runs the given args in a subprocess.Popen, and then calls the function
	on_exit when the subprocess completes.
	on_exit is a callable object, and popen_args is a list/tuple of args that
	would give to subprocess.Popen.
	"""
	def run_in_thread(on_exit, popen_args):
		proc = subprocess.Popen(*popen_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()
		errcode = proc.returncode
		proc.wait()
		#print("output", out)
		#print("error", err)
		#print("error code", errcode)
		on_exit()
		return
	thread = threading.Thread(target=run_in_thread, args=(on_exit, popen_args))
	thread.start()
	# returns immediately after the thread starts
	return thread
