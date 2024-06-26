#!/usr/bin/env python
 
import subprocess, sys
from classes.Daemon import Daemon
from config import Config, ENV


class RobotDaemon(Daemon):
    def run(self):
        print("Running daemon: %s" % Config.MAIN_PATH);
        subprocess.run([ENV.PYTHON, Config.MAIN_PATH])


daemon = RobotDaemon('/dev/null', Config.LOGS_PATH, Config.ERRORS_PATH)

if len(sys.argv) == 2:
    if 'start' == sys.argv[1]:
        daemon.start()
    elif 'stop' == sys.argv[1]:
        daemon.stop()
    elif 'restart' == sys.argv[1]:
        daemon.restart()
    else:
        print("Unknown command")
        sys.exit(2)
    sys.exit(0)
else:
    print("usage: %s start|stop|restart" % sys.argv[0])
    sys.exit(2)
