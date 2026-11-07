"""One lock orders rejection, command transmission and case boundaries."""
import threading


class Admission:
    def __init__(self):
        self.lock = threading.RLock()
        self.blocked = True
        self.active = False
        self.fatal = False

    def begin(self):
        with self.lock:
            if self.active or self.fatal:
                raise RuntimeError('admission cannot begin after incomplete/fatal case')
            self.active = True
            self.blocked = False

    def reject(self, fatal=False):
        with self.lock:
            self.blocked = True
            self.fatal = self.fatal or fatal or not self.active

    def send(self, pipe, payload, record):
        with self.lock:
            if self.blocked or not self.active or self.fatal:
                return False
            try:
                pipe.write(payload)
                pipe.flush()
                record()
            except BaseException:
                self.blocked = True
                self.fatal = True
                raise
            return True

    def end(self, expected_and_closed):
        with self.lock:
            self.blocked = True
            self.active = False
            self.fatal = self.fatal or not expected_and_closed
