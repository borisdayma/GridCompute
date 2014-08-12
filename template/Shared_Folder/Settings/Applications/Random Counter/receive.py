'''Template for receiving cases that have been processed on the grid'''

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


# These modules are only required for below example
import pathlib
import os.path


def receive_case(output_files):
    """Receive a case from the grid.
    
    This function receives a case that has been processed on the grid. 
    Process is executed in a temporary folder where all files are copied.
    
    Args:
        output_files: ordered list (or tuple) of output files path
    """

    # In this example, we know that the output is a single file which contains file size of all inputs
    # we will append (or create) the results to file 'gridcompute_output.txt' in home directory
    
    case_output_file = pathlib.Path(output_files[0])
    with case_output_file.open(mode='r', encoding='utf8') as f:
        data = f.read()
    
    general_output_file = pathlib.Path(os.path.expanduser('~')) / 'gridcompute_output.txt'
    with general_output_file.open(mode='a') as f:
        print(data, file = f)

