import sys
from cx_Freeze import setup, Executable

import g_config

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


