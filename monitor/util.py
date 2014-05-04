import threading
from contextlib import contextmanager

from main import event_loop
from monitor_meta import hooks
from monitor.main import event_loop, send_exit, pp

@contextmanager
def event_loop_thread():
    event_loop_thread = threading.Thread(target=event_loop, args=(hooks,))
    pp('starting event loop thread')
    event_loop_thread.start()
    yield
    send_exit()
    pp('joining event loop thread')
    event_loop_thread.join()
