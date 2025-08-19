
from typing import Callable
import threading, time

class SimpleScheduler:
    """ Çok basit bir zamanlayıcı (cron benzeri değil). Demo amaçlı. """
    def every_seconds(self, seconds: int, fn: Callable, *args, **kwargs):
        def loop():
            while True:
                fn(*args, **kwargs)
                time.sleep(seconds)
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        return t
