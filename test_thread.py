import validate_threading_functions as vthread

def end_thread():
	print("this process is complete")
	return

vthread.popen_and_call(end_thread, ["echo", "wooga"])
