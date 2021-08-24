import time
import logging.handlers
import logging
import os
import multiprocessing

# Once a process has acquired a lock, subsequent attempts to acquire it from any process will block until it is released
lock_Rollover = multiprocessing.Lock()


class MultiProcessSafeTimedRotatingFileHandler(
    logging.handlers.TimedRotatingFileHandler
):
    """
    Custom handler to override the default logging.handlers.TimedRotatingFileHandler as it is not safe
    to use with multiprocess.
    We are currently using 6 processes and we have to let only one process to deal with logging into one specific file
    instead of trying to do logging from all or more than one process at a time.
    """

    def __init__(
        self,
        filename,
        when="h",
        interval=1,
        backupCount=0,
        encoding=None,
        delay=False,
        utc=False,
        atTime=None,
    ):
        super().__init__(
            filename, when, interval, backupCount, encoding, delay, utc, atTime
        )
        filename = self.baseFilename
        if os.path.exists(filename):
            line = open(filename, "r").readline()
            if line == "":
                t = int(time.time())
            else:
                n = line.find(",")
                line = line[:n]
                t = int(time.mktime(time.strptime(line, "[%Y-%m-%d %H:%M:%S")))

        else:
            t = int(time.time())
        self.rolloverAt = self.computeRollover(t)

    def emit(self, record):
        """
        Emit a record.
        Output the record to the file, catering for rollover as described
        in doRollover().
        """
        try:
            if self.shouldRollover(record):
                if self.stream:
                    self.stream.close()
                    self.stream = None
                with lock_Rollover:
                    f = open(self.baseFilename, "r")

                    line = f.readline()
                    if line == "":
                        f.close()
                        self.doRollover()
                    else:
                        f.close()

                        n = line.find(",")
                        line = line[:n]
                        t = int(time.mktime(time.strptime(line, "[%Y-%m-%d %H:%M:%S")))

                        now = int(time.time())
                        if t >= self.rolloverAt:
                            if self.computeRollover(t) <= now:
                                self.rolloverAt = self.computeRollover(t)
                                self.doRollover()
                            else:
                                self.rolloverAt = t
                                self.stream = self._open()
                        else:
                            if self.computeRollover(t) >= now:
                                self.rolloverAt = t
                                self.stream = self._open()
                            else:
                                self.doRollover()

            logging.FileHandler.emit(self, record)
        except Exception:
            self.handleError(record)
