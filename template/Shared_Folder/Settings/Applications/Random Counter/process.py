'''Template for processing cases received from the grid'''

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
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# For any question, please contact Boris Dayma at boris.dayma@gmail.com


# These modules are only required for below example
import os.path
import pathlib
import getpass, platform
import random, time


def process_case(input_files):
    """Process a case and return its results.
    
    This function process a case from the grid and returns a list of output files that are
    sent back to the server. Process is executed in a temporary folder where all files are
    copied.
    
    Args:
        input_files: ordered list (or tuple) of input files path
        
    Returns:
        An ordered list (or tuple) of output files to return to the server.
    """

    # In this example, we will count down from a random number. The output will be a single file which
    # contains file name, who processed the file, and results of program.
    folder = pathlib.Path(input_files[0]).parent
    output_file = pathlib.Path(folder) / 'output.txt'

    # Create some CPU intensive task
    start=time.time()
    random.seed()
    n=random.randint(100000000,250000000)
    countdown(n)
    end=time.time()
    total = end - start

    with output_file.open(mode='w', encoding='utf8') as f_output:
        print('Processed with Random Counter by {0} on {1}:'.format(getpass.getuser(), platform.node()), file = f_output)
        for input_file in input_files:
            print('{0}'.format(pathlib.Path(input_file).name), file = f_output)
        print('Counter set to {}, run time: {}'.format(n, total), file=f_output)

    output_file_path = str(output_file)
    return (output_file_path,)   # generator of files to return as output files


# This is an auxiliary function required only for this example
def countdown(n):
    while n>0:
        n -=1

