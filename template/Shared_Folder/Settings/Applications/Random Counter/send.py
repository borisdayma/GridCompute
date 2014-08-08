'''\
This module is a template for sending cases to the grid.
Copyright 2014 Boris Dayma

Function executed from this module is select_input_files
'''


def select_input_files(filepath):
    """
    This function takes filepath as argument and returns a generator (list, tuple…) of cases to run. Each case to run is a generator (list, tuple) of file paths that will be needed as input for the specific case
    """

    # in this example, only one case is returned, and that case contains only one file (the file selected)

    case_1 = (filepath,)      # list of input files needed for case_1
    return (case_1,)          # list of cases to run



