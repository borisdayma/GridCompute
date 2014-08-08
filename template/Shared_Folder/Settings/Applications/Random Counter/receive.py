'''\
This module is a template for receiving cases that have been processed.
Copyright 2014 Boris Dayma

Function executed from this module is receive_case.

Note: this function should be fast to return as only one process is allocated to receiving results
'''


# These modules are only required for below example
import pathlib
import os.path

def receive_case(output_files):
    """
    This function takes output_files as argument, which is the list of output files (full path) associated with a case. All files are copied to a temporary directory.
    """

    # in this example, we know that the output is a single file which contains file size of all inputs
    # we will append (or create) the results to file 'gridcompute_output.txt' in home directory
    
    case_output_file = pathlib.Path(output_files[0])
    with case_output_file.open(mode='r', encoding='utf8') as f:
        data = f.read()
    
    general_output_file = pathlib.Path(os.path.expanduser('~')) / 'gridcompute_output.txt'
    with general_output_file.open(mode='a') as f:
        print(data, file = f)

