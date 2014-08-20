'''This module gathers configuration variables used in the other modules.

It is used to share global variables and edit configuration variables easier.
 
Attributes:
          program_name: Name of the program.
          version: Current version.
          author: Author of the program.
          copyright: Copyright.
          title_windows: Title displayed on windows.
          max_number_process: Maximal number of parallel process that can be executed on this computer.
          gui_refresh_interval: Refresh rate of interface in milliseconds.
          db_connect_frequency: Time in seconds before database is accessed again if no case/result is found.
          db_heartbeat_frequency: Frequency in seconds that heartbeat are sent on running processes to notify
                                database that they are still alive.
          db_heatbeat_dead: Time in seconds without heartbeat after which we consider a process is dead.
          daemon_pause: Time in seconds between each process of daemons.
          log_path: Path of the log file.
          pid_file: Path of the file keeping pid of the program to ensure there is only one single instance
                  running.
          '''

# Copyright 2014 Boris Dayma
# 
# This file is part of GridCompute.
# 
# GridCompute is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# GridCompute is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with GridCompute.  If not, see <http://www.gnu.org/licenses/>.
#
# For any question, please contact Boris Dayma at boris.dayma@gmail.com


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
max_number_process = multiprocessing.cpu_count()
gui_refresh_interval = 500


# Server variables

db_connect_frequency = 30
db_heartbeat_frequency = 60
db_heartbeat_dead = 60 + db_heartbeat_frequency
daemon_pause = 2


# Log variables

log_path = pathlib.Path(tempfile.gettempdir()) / 'GridCompute' / 'gridcompute.log'
pid_file = pathlib.Path(tempfile.gettempdir()) / 'GridCompute' / 'pid'
