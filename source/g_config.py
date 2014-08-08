'''
Configuration variables used in other modules

Copyright 2014 Boris Dayma
'''


import multiprocessing
import pathlib
import tempfile


# Program variables

program_name = "Gridcompute"
version = '0.2'
author = "Boris Dayma"
copyright = "Copyright 2014 Boris Dayma"


# GUI variables

title_windows = "{} v{}".format(program_name, version)
max_number_process = multiprocessing.cpu_count()       # max number of parallel process
gui_refresh_interval = 500                             # interval in milliseconds to refresh gui


# Server variables

db_connect_frequency = 30    # time (sec) before db is accessed again if no case/result is found
db_heartbeat_frequency = 60  # frequency (sec) heartbeat are sent on running process to notify database that they are still alive
db_heartbeat_dead = 60 + db_heartbeat_frequency # time (sec) without heartbeat after which we consider a process is dead
daemon_pause = 2             # time (sec) between each process of daemons


# Log variables

log_path = pathlib.Path(tempfile.gettempdir()) / 'GridCompute' / 'gridcompute.log'  # path of log file
pid_file = pathlib.Path(tempfile.gettempdir()) / 'GridCompute' / 'pid'  # path of file keeping pid of program to allow only a single instance
