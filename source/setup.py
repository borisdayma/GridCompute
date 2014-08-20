'''This script is used for building the executuble with cx_Freeze.
 
Please refer to the section "Development" of the documentation for building the application.'''

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


import sys
from cx_Freeze import setup, Executable

import g_config


if __name__ == "__main__":

    base = None
    # TODO uncomment to hide console (+ refer to filed bug)
    #if sys.platform == 'win32':
    #    base = 'Win32GUI'

    include_files = [('server_template.txt', 'server.txt'), ('licenses', 'licenses')]

    name_executable = 'GridCompute.exe' if sys.platform == 'win32' else 'GridCompute'

    setup(name=g_config.program_name,
          version=g_config.version,
          description='Quick implementation of Grid Computing',
          author=g_config.author,
          options = {'build_exe': {'include_files':include_files, 'include_msvcr': True, 'optimize':2}}, 
          executables=[Executable('main.py', base=base, targetName=name_executable)]
          )


