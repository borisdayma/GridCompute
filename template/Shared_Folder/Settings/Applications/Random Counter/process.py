'''\
This module is a template for processing cases received from the grid.
Copyright 2014 Boris Dayma

Function executed from this module is process_case
'''


# These modules are only required for below example
import os.path
import pathlib
import getpass, platform
import random, time


def process_case(input_files):
    """
    This function takes input_files as argument, which is a list of all the input files (full path) necessary to run the case and returns a generator (list, tuple) of output file paths. Those input files have been copied to a temporary directory.
    """

    # in this example, we will count down from a random number. The output will be a single file which contains file name, who processed the file, and results of program.
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

