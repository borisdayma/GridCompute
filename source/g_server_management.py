'''This module contains all server related functionalities.
 
It creates server variables associated to file server and mongo database
and handle the communication with them.'''

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


import csv
import datetime
import getpass
import importlib
import multiprocessing
import os
import pathlib
import platform
import shutil
import sys
import tempfile
import time
import zipfile, zlib

import bson
import psutil
import pymongo

import g_config as config


class Server:
    '''Class handling server-related functionalities.

    File server path is taken from "server.txt" present at root of program.  Settings are taken from
    "settings.txt" present on the file server.
    
    Server properties are set at initialization.

    Args:
        event_queue: queue of events to process by gui
        gui_dedicated_process: number of dedicated process selected in gui
        daemon_dedicated_process: number of dedicated process communicated to daemon process
        exit_program: variable scanned by daemons to know when to exit
        gui_answer: notify when gui answered a question
        server_path: path of file server as defined in "server.txt" file
        app_path: path of applications-specific scripts
        settings_path: path of settings.txt file
        settings: list of settings from settings.txt on file server including:

                  - mongodb server: Address of the mongo instance including connection port containing
                    "gridcompute" like ``mongodbserver.com:888`` or ``10.0.0.1:888`` or ``Machine123:888``.
                  - user group: Login used to connect on mongo database.
                  - password: Password used to connect on mongo database.
                  - instance: Data instance to consider like ``0`` or ``debug``.

        mongodb: Connection to mongo database
        server_functions: Dictionary of application-specific scripts. The key is application name and value is
                        a dictionary of following keys:

                        - path: path of application folder
                        - send, process, receive: booleans corresponding to existence of these functions

        software_allowed_to_run: set of applications that can run as defined in "Software_Per_Machine.csv"
    '''

    def __init__(self, event_queue, dedicated_process):
        
        self.event_queue = event_queue
        self.gui_dedicated_process = dedicated_process
        self.gui_dedicated_process.trace('w', self.notify_number_process_daemon)
        self.daemon_dedicated_process = multiprocessing.Value('i', 0)
        self.exit_program = multiprocessing.Event()
        self.exit_program.clear()
        self.gui_answer = multiprocessing.Event()

        server_file = pathlib.Path("server.txt")
        if not server_file.is_file():
            self.event_queue.put({'type':'critical', 'message':'File server.txt not found in current directory'})
            raise SystemExit
        with server_file.open() as f:
            server_path_name = f.read().strip()
        self.server_path = pathlib.Path(server_path_name)
        if not self.server_path.is_dir():
            self.event_queue.put({'type':'critical', 'message':'File server.txt does not define an accessible directory'})
            raise SystemExit
        settings_folder = self.server_path / "Settings"
        if not settings_folder.is_dir():
            self.event_queue.put({'type':'critical', 'message':'Settings folder not found at\n{}'.format(str(settings_folder))})
            raise SystemExit

        self.app_path = self.server_path / "Settings" / "Applications"
        self.settings_path = self.server_path / "Settings" / "settings.txt"
        sys.path.insert(0, str(self.app_path))  # allow to load app-specific scripts easily
        self.settings = self.get_settings()
        self.mongodb = self.access_mongodb()
        self.handle_software_permissions()
        self.server_functions = self.scan_applications()
        self.software_allowed_to_run = self.get_software_allowed_to_run()
        self.event_queue.put({'type':'info', 'message':'Logged on grid "{}" instance "{}"'.format(self.settings['user group'], self.settings['instance'])})

        self.create_daemons()  # daemons can start

    def notify_number_process_daemon(self, *args):
        '''Notify the daemon process of a change of number of processes selected in GUI.'''

        self.daemon_dedicated_process.value = int(self.gui_dedicated_process.get())

    def get_settings(self):
        '''Initialize settings variable from "settings.txt" present on server.'''

        if not self.settings_path.is_file():
            self.event_queue.put({'type':'critical', 'message':'File settings.txt not found in Settings directory'})
            raise SystemExit
        with self.settings_path.open() as f:
            settings = {value[0].strip():value[-1].strip() for value in
                    (line.split(":", 1) for line in f.read().strip().split('\n'))}

        required_settings = {'mongodb server', 'instance', 'user group', 'password'}
        if not all(k in settings for k in required_settings):
            missing_settings = required_settings - settings.keys()
            self.event_queue.put({'type':'critical', 
                                 'message':'"settings.txt" missing data:\n{}'.format(
                                     '\n'.join('"{}"'.format(x) for x in missing_settings))})
            raise SystemExit
        self.event_queue.put({'type':'info', 'message':'Accessed "settings.txt" properties'})
        return settings

    def access_mongodb(self):
        '''Access the mongo database.'''

        try:
            mongodb = pymongo.MongoClient("{}".format(self.settings['mongodb server'])).gridcompute
        except:
            self.event_queue.put({'type':'critical',
                                 'message':'Database currently not accessible.\nPlease check your connection and "mongodb server" setting.'})
            raise SystemExit
        try:
            mongodb.authenticate(self.settings['user group'], self.settings['password'])
        except:
            self.event_queue.put({'type':'critical',
                                 'message':'You are not authorized to use this software.\nPlease check "user group" and "password" settings.'})
            raise SystemExit
        self.event_queue.put({'type':'info', 'message':'Accessed mongo database'})
        return mongodb

    def handle_software_permissions(self):
        '''Verify that mongo database allows current version of program to run.
        
        This is based on the collection "versions" present in mongo database.
        If "versions" collection is not present, a warning is displayed.'''

        if 'versions' not in self.mongodb.collection_names():
            self.event_queue.put({'type':'warning',
                                'message':'Mongo database does not contain a "versions" collection.\nData may be corrupted and program unstable.'})

        version = self.mongodb.versions.find_one({'_id':str(config.version)})
        if version is None:
            self.event_queue.put({'type':'critical', 'message':'Error: Version {} is not valid'.format(config.version)})
            raise SystemExit
        elif version['status'] == 'warning':
            self.event_queue.put({'type':'warning', 'message':version['message']})
        elif access['status'] == 'refused':
            self.event_queue.put({'type':'critical', 'message':version['message']})
            raise SystemExit
        else:
            self.event_queue.put({'type':'info', 'message':'Current version of program is valid'})

    def scan_applications(self):
        '''Scan application specific scripts present on file server.'''

        application_folders = (folder for folder in self.app_path.glob("*") if folder.is_dir())
        applications = ({folder.name : {"path" : folder, "send" : (folder / "send.py").is_file(),
                                        "process" : (folder / "process.py").is_file(),
                                        "receive" : (folder / "receive.py").is_file()}
                        for folder in application_folders})
        self.event_queue.put({'type':'info', 'message':'Scanned application specific scripts'})
        return applications

    def applications_with_send(self):
        '''Return a dictionary of applications that have a send function.

        The key is the application name and the value is the script path.'''

        return {app : (self.server_functions[app]["path"] / "send.py") for app in self.server_functions if self.server_functions[app]["send"]}

    def applications_with_process(self):
        '''Return a dictionary of applications that have a process function.

        The key is the application name and the value is the script path.'''

        return {app : (self.server_functions[app]["path"] / "process.py") for app in self.server_functions if self.server_functions[app]["process"]}

    def applications_with_receive(self):
        '''Return a dictionary of applications that have a receive function.

        The key is the application name and the value is the script path.'''

        return {app : (self.server_functions[app]["path"] / "receive.py") for app in self.server_functions if self.server_functions[app]["receive"]}

    def get_software_allowed_to_run(self):
        '''Return the list of software allowed to run on this machine per "Software_Per_Machine.csv"
        present on file server.'''

        self.event_queue.put({'type':'info', 'message':'Obtaining software allowed to run on this machine'})
        self.event_queue.put({'type':'info', 'message':'Machine identified as "{}"'.format(platform.node())})
        file_matrix = self.server_path / "Settings" / "Software_Per_Machine.csv"
        if not file_matrix.is_file():
            self.event_queue.put({'type':'error', 'message':'File "Software_Per_Machine.csv" not found in Settings folder on server'})
            return set()
        with file_matrix.open() as csv_file:
            machine_name = platform.node()
            dict_reader = csv.DictReader(csv_file)
            for row in dict_reader:
                if "Machine name" not in row:
                    self.event_queue.put({'type':'error', 'message':'Column "Machine name" not defined in "Software_Per_Machine.csv'})
                    return set()
                elif row["Machine name"].upper() == machine_name.upper():
                    return {app for app,value in row.items() if value=="1"}
            return set()

    def create_daemons(self):
        '''Create daemons required in the application.
        
        Two daemons are created:
            
            - Daemon process: scans continuously database to check if there are new calculations to
              perform (if number of processes selected allows it).
            - Daemon receive: scans continuously database to check if there are new results to receive.'''

        multiprocessing.Process(target=run_daemon_receive,
                               args=(self.applications_with_receive(),
                                    self.event_queue,
                                    self.exit_program,
                                    self.server_path,
                                    self.settings)).start()
        multiprocessing.Process(target=run_daemon_process,
                               args=(self.applications_with_process(),
                                    self.daemon_dedicated_process,
                                    self.event_queue,
                                    self.exit_program,
                                    self.gui_answer,
                                    self.server_path,
                                    self.settings,
                                    self.software_allowed_to_run)).start()
        self.event_queue.put({'type':'info', 'message':'Created daemons'})

    def submit_to_server(self, cases_to_submit, application, keep_running = True):
        '''Submit cases to the server.
        
        Input files are zipped and copied to the file server. Cases are entered in mongo database.
        
        Args:
            cases_to_submit: List of cases. Each case is a list of input files associated to a case.
            application: Application associated to input files.
            keep_running: Argument that can be associated to the state of a variable.
                        When this variable is False, function ends.
                        It is used to catch when user closes the progress window.'''

        n_cases_submitted = 0  # keep track of number of cases submitted until end of function (or user closes progress window)       
        for (count, (gui_case, case_files)) in enumerate(cases_to_submit):
            if not keep_running:
                break
            self.event_queue.put({'type':'change progress', 'progress increment':1,
                'progress label':'submitting case {}/{}'.format(count+1, len(cases_to_submit))})

            with tempfile.TemporaryDirectory() as temp_directory:  # create a temporary folder to create zip file
                zip_path = str(pathlib.Path(temp_directory) / "input_files")
                with zipfile.ZipFile(zip_path, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_case:
                    for input_number, input_file in enumerate(case_files):
                        if not keep_running:
                            break
                        if pathlib.Path(input_file).is_file():                 # if this is a file, we just write it
                            zip_case.write(input_file, arcname = '{}_{}'.format(
                                input_number, pathlib.Path(input_file).name))  # add position of file in its name
                        elif pathlib.Path(input_file).is_dir():                # if this is a folder, we write full structure
                            if not tuple(pathlib.Path(input_file).iterdir()):  # if folder empty, we just write empty folder
                                zif = zipfile.ZipInfo('{}_{}/'.format(input_number, pathlib.Path(input_file).name))
                                zip_case.writestr(zif, '')
                            else:                                              # if this is a folder with contents
                                empty_dirs = []                                # we keep track of all the empty directories
                                for root, dirs, files in os.walk(input_file):
                                    empty_dirs.extend([dir for dir in dirs if not tuple((pathlib.Path(root) / dir).iterdir())])
                                    for name in files:
                                        full_path = pathlib.Path(root) / name
                                        archive_path = pathlib.Path('{}_{}'.format(
                                            input_number, pathlib.Path(input_file).name)) / full_path.relative_to(pathlib.Path(input_file))
                                        zip_case.write(str(full_path), arcname = str(archive_path))
                                    for dir in empty_dirs:
                                        full_path = pathlib.Path(root) / dir
                                        archive_path = pathlib.Path('{}_{}/'.format(
                                            input_number, pathlib.Path(input_file).name)) / full_path.relative_to(pathlib.Path(input_file))
                                        zif = zipfile.ZipInfo('{}/'.format(archive_path))
                                        zip_case.writestr(zif, '')
                                    empty_dirs = []

                # create folder structure if not existing: "Cases/user/machine/case"
                cases_folder_relative_to_server = pathlib.Path("Cases") / getpass.getuser().upper() / platform.node().upper()
                cases_folder_absolute = self.server_path / cases_folder_relative_to_server
                os.makedirs(str(cases_folder_absolute), exist_ok = True)

                if not keep_running:
                    break

                # copy case on file server with a unique name
                case_path_relative_to_server = cases_folder_relative_to_server / str(bson.ObjectId())
                case_path_absolute = self.server_path / case_path_relative_to_server
                shutil.copy(src = zip_path, dst = str(case_path_absolute))

                if not keep_running:
                    break

                # add case on database
                db_case = {"user_group" : self.settings['user group'],
                        "instance" : self.settings['instance'],
                        "status" : "to process",
                        "application": application,
                        "origin" : {"machine" : platform.node(), "user" : getpass.getuser(),
                                   'path':pathlib.Path(case_files[0]).as_posix(),
                                   'time':{'start':datetime.datetime.now(), 'end':datetime.datetime(1, 1, 1)}},
                        "processors" : {'processor_list':[],
                                       "time":{'start':datetime.datetime.now(), 'end':datetime.datetime(1, 1, 1)}},
                        'last_heartbeat' : datetime.datetime(1, 1, 1),
                        'path' : case_path_relative_to_server.as_posix()}  # path name standardized
                self.mongodb.cases.insert(db_case)

                self.event_queue.put({'type':'submitted case', 'case':gui_case})  # update gui
                n_cases_submitted += 1

        self.event_queue.put({'type':'close progress'})
        self.event_queue.put({'type':'info', 'message box':True,
                                    'message':'1 case has been submitted successfully' if n_cases_submitted == 1
                                    else '{} cases have been submitted successfully'.format(n_cases_submitted)})

    def add_cases(self, files_selected, application, keep_running = True):
        '''Add a list of cases to interface from files selected by user.
        
        A file selected can correspond to one or several cases to run. Each case being a list of input files.
        Those cases are sent to the interface which displays the first input file of each case.
        The application specific "send.py" function is used on each file selected.
        
        Args:
            files_selected: Files selected by user
            application: Application associated to input files
            keep_running: Argument that can be associated to the state of a variable.
                        When this variable is False, function ends.
                        It is used to catch when user closes the progress window.'''

        try:
            send_module = return_module(application, "send")  # return app-specific send module
        except:
            self.event_queue.put({'type':'close progress'})
            self.event_queue.put({'type':'error',
                                 'message':'Error while importing "{}" send module'.format(application)})
            return
        for count, file_selected in enumerate(files_selected):
            if not keep_running:
                break
            self.event_queue.put({'type':'change progress', 'progress increment':1,
                'progress label':'getting cases from file {}/{}'.format(count+1, len(files_selected))})
            try:
                new_cases = send_module.select_input_files(file_selected)
            except:
                self.event_queue.put({'type':'close progress'})
                self.event_queue.put({'type':'error',
                                     'message':'Error while executing "select_input_files" from "{}" send module'.format(application)})
                return
            if type(new_cases) == type('') or not len(new_cases) or type(new_cases[0]) == type(''): # check return a list of cases (list of list of files)
                self.event_queue.put({'type':'close progress'})
                self.event_queue.put({'type':'error',
                                     'message':'"select_input_files" from "{}" send module did not return a list of cases (each of these cases must be defined as a list of files)'.format(application)})
                return
            for new_case in new_cases:
                self.event_queue.put({'type':'add case', 'case':new_case})
        self.event_queue.put({'type':'close progress'})
        self.event_queue.put({'type':'log_file_only', 'message':'Added cases to interface'})

    def refresh_my_cases(self, keep_running = True):
        '''Refresh "my cases" list.
        
        Access mongo database to display all user cases that have not been totally processed yet (ie not received by user).

        Args:
            keep_running: Argument that can be associated to the state of a variable.
                        When this variable is False, function ends.
                        It is used to catch when user closes the progress window.'''

        total_to_process, total_to_receive = 0, 0
        count_process = 0  # keep track of position of case to process in mongo database (ordered by submission date)
        for case in self.mongodb.cases.find(spec = {
            "user_group":self.settings['user group'], 'instance':self.settings['instance'], 
            "status":{"$in":['to process', 'processing', 'processed']}},
            fields=['status', 'application', 'origin.user', 'origin.machine', 'origin.path', 'processors.processor_list'], 
            sort= [("_id",pymongo.ASCENDING)]):
        
            if not keep_running:
                break
            if case['status'] == 'to process':
                count_process += 1
            if case['origin']['user'] == getpass.getuser() and case['origin']['machine'] == platform.node():
                if case['status'] == 'processed':
                    total_to_receive += 1
                else:
                    total_to_process += 1
                processor = '' if not case['processors']['processor_list'] else case['processors']['processor_list'][-1]['user']  # get latest processor (in case it failed)
                status = case['status'] if case['status'] != 'to process' else 'wait #{}'.format(count_process)  # set to position in wait list
                self.event_queue.put({'type':'add my case', 'cases to process': total_to_process, 'cases to receive': total_to_receive, 
                                     'case':case['origin']['path'], 'application':case['application'], 'processor': processor, 'status':status})
        self.event_queue.put({'type':'close progress'})
        self.event_queue.put({'type':'log_file_only', 'message':'Refreshed "my cases" tab'})
    
    def create_report(self, file_report, keep_running = True):
        '''Create a report of cases present on database.

        Display cases and their details from database, limited to the ones from same "user group".

        Args:
            keep_running: Argument that can be associated to the state of a variable.
                        When this variable is False, function ends.
                        It is used to catch when user closes the progress window.'''

        number_cases = self.mongodb.cases.find({'user_group':self.settings['user group']}).count()
        self.event_queue.put({'type':'change progress max', 'progress maximum':number_cases})

        # Headers
        columns = ['Server Instance', 'Application', 'Current Path', 'Last signal to server',
                'User Origin', 'Machine Origin', 'Path Origin', 'Current status',
                'Time submitted by originator', 'Time started to process',
                'Time finished to process', 'Time received by originator',
                'Number of attempts to process', 'Processor User 1', 'Processor Machine 1',
                'Processor User 2', 'Processor Machine 2', 'Processor User 3', 'Processor Machine 3']

        with open(file_report, mode='w', encoding='utf8') as f:
            print('Status of {}\n\n'.format(self.settings['user group']), file = f)
            print('\t'.join(columns), file = f)

            for (count, case) in enumerate(self.mongodb.cases.find(
                spec = {'user_group':self.settings['user group']}, sort= [("_id",pymongo.ASCENDING)])):
                if not keep_running:
                    break

                self.event_queue.put({'type':'change progress', 'progress increment':1,
                    'progress label':'downloading case {}/{}'.format(count+1, number_cases)})
                data=dict()
                data['Server Instance'] = case['instance']
                data['Application'] = case['application']
                data['Current Path'] = case['path']
                data['Last signal to server'] = '' if case['last_heartbeat'] == datetime.datetime(1, 1, 1) else case['last_heartbeat']
                data['User Origin'] = case['origin']['user']
                data['Machine Origin'] = case['origin']['machine']
                data['Path Origin'] = case['origin']['path']
                data['Current status'] = case['status']
                data['Time submitted by originator'] = case['origin']['time']['start']
                data['Time started to process'] = '' if case['processors']['time']['start'] == datetime.datetime(1, 1, 1) else case['processors']['time']['start']
                data['Time finished to process'] = '' if case['processors']['time']['end'] == datetime.datetime(1, 1, 1) else case['processors']['time']['end']
                data['Time received by originator'] = '' if case['origin']['time']['end'] == datetime.datetime(1, 1, 1) else case['origin']['time']['end']
                processors = case['processors']['processor_list']
                data['Number of attempts to process'] = len(processors)                
                data['Processor User 1'] = ''
                data['Processor Machine 1'] = ''
                data['Processor User 2'] = ''
                data['Processor Machine 2'] = ''
                data['Processor User 3'] = ''
                data['Processor Machine 3'] = ''
                if processors:
                    data['Processor User 1'] = processors[0]['user']
                    data['Processor Machine 1'] = processors[0]['machine']
                if len(processors) >= 2:
                    data['Processor User 2'] = processors[1]['user']
                    data['Processor Machine 2'] = processors[1]['machine']
                if len(processors) >= 3:
                    data['Processor User 3'] = processors[2]['user']
                    data['Processor Machine 3'] = processors[2]['machine']
                print('\t'.join(str(data[k]) for k in columns), file = f)

        self.event_queue.put({'type':'close progress'})
        self.event_queue.put({'type':'info', 'message':'Created report from database in {}'.format(str(pathlib.Path(file_report))), 'message box':True})

    def exit_processes(self):
        '''Terminate program.
        
        Ensure daemon process (and its child processes) and daemon receive terminate properly.'''

        self.exit_program.set()  # This value is scanned by daemons to know when to exit
        for p in multiprocessing.active_children():
            p.join()
        try:
            os.remove(str(config.pid_file))
        except OSError:
            pass
        self.event_queue.put({'type':'exit'})

def check_quit_program(exit_program):
    '''Function used by daemons to check if they need to terminate and kill their child processes.
    
    Args:
        exit_program: Variable scanned by daemons to know when to exit.'''
    
    if exit_program.is_set():
        for p in multiprocessing.active_children():
            p.terminate()
        for p in multiprocessing.active_children():
            p.join(1)
        raise SystemExit

def refresh_status_daemon_process(alive_process, dedicated_process, event_queue, exit_program, gui_answer, paused_process):
    '''Refresh status variables used by daemon process.
    
    Args:
        alive_process: List of processes alive.
        dedicated_process: Number of dedicated process selected in gui.
        event_queue: Queue of events to process by gui.
        exit_program: Variable scanned by daemons to know when to exit.
        gui_answer: Notify when gui answered a question.
        paused_process: List of processes currently on pause.
    '''
    
    check_quit_program(exit_program)

    # Notifies user if process need to be stopped when user select 0 process
    if not dedicated_process.value and len(multiprocessing.active_children()):
        gui_answer.clear()
        event_queue.put({'type':'terminate process?'})
        gui_answer.wait()
        if not dedicated_process.value:            # user confirmed all processes need to terminate
            if len(multiprocessing.active_children()):
                event_queue.put({'type':'info', 'message':'Terminating every running process'})
                for p in multiprocessing.active_children():
                    p.terminate()
                for p in multiprocessing.active_children():
                    p.join()
                while multiprocessing.active_children():
                    time.sleep(1)    # ensure all process have finished
                paused_process = []  # ensure that list is empty if process not terminated yet

    # Update paused_process. Check that processes paused are actually not terminated
    for p in paused_process:
        if not p.is_alive():
            paused_process.remove(p)

    # Check whether running processes displayed in GUI have finished
    for p in alive_process:
        if p['process'].is_alive():
            # send heartbeat to mongodb on each case if it has been long enough
            if (datetime.datetime.now() - p['last heartbeat']).total_seconds() > config.db_heartbeat_frequency:
                mongodb.cases.update({'_id':p['_id']}, {'$set': {'last_heartbeat': datetime.datetime.now()}})
                p['last heartbeat'] = datetime.datetime.now()
        else:
            event_queue.put({'type':'remove my process', 'pid':p['process'].pid})
            alive_process.remove(p)

def run_daemon_process(applications_with_process, dedicated_process, event_queue, exit_program, gui_answer, server_path, settings, software_allowed_to_run):
    '''Run "daemon process" that launches new processes when possible.
    
    Daemon process runs continuously and check on database if processes are available to launch when user allows it.
    
    Args:
        applications_with_process: dictionary of applications that have a process function
        dedicated_process: number of dedicated process selected in gui
        event_queue: queue of events to process by gui
        exit_program: variable scanned by daemons to know when to exit
        gui_answer: notify when gui answered a question
        server_path: path of file server as defined in "server.txt" file
        settings: list of settings from settings.txt on file server
        software_allowed_to_run: set of applications that can run as defined in "Software_Per_Machine.csv"
    '''

    event_queue.put({'type':'log_file_only', 'message':'Starting daemon process'})
    if not (len(software_allowed_to_run) * len(applications_with_process)):
        # current machine will not be able to process any case
        event_queue.put({'type':'info', 'message box':True, 'message':'Possible applications to perform calculations: None'})
        return
    possible_apps = list(software_allowed_to_run & set(applications_with_process.keys()))
    possible_apps.sort()
    event_queue.put({'type':'info', 'message':'Possible applications to perform calculations: {}'.format(possible_apps)})

    # create new connection
    mongodb = pymongo.MongoClient('{}'.format(settings['mongodb server'])).gridcompute
    mongodb.authenticate(settings['user group'], settings['password'])

    last_access_no_case = datetime.datetime(1, 1, 1)  # last time db was accessed and no case was present
    paused_process = []  # keep track of all processes that have been paused
    alive_process = []   # keep track of all processes that are alive

    while True:
        refresh_status_daemon_process(alive_process, dedicated_process, event_queue, exit_program, gui_answer, paused_process)
        time.sleep(config.daemon_pause)
        refresh_status_daemon_process(alive_process, dedicated_process, event_queue, exit_program, gui_answer, paused_process)

        # some process might need to pause (if user decreased number of allowed processes)
        if dedicated_process.value < (len(multiprocessing.active_children()) - len(paused_process)):

            # get process that we can pause
            p_children = multiprocessing.active_children()
            p_possible_new_pause = [p for p in p_children if p not in paused_process]

            for i in range(len(p_children) - len(paused_process) - dedicated_process.value):
                try:  # ensure does not fail in case process terminated unexpectedly
                    event_queue.put({'type':'info', 'message':'Pausing one process'})
                    psutil.Process(p_possible_new_pause[i].pid).suspend()
                    paused_process.append(p_possible_new_pause[i])
                    event_queue.put({'type':'change my process', 'pid':p_possible_new_pause[i].pid, 'status':'paused'})
                    event_queue.put({'type':'log_file_only', 'message':'Paused one process'})
                except:
                    pass

        # some process might need to be created or restart
        elif dedicated_process.value > (len(multiprocessing.active_children()) - len(paused_process)):

            # restart process
            while paused_process and (dedicated_process.value > (len(multiprocessing.active_children()) - len(paused_process))):
                event_queue.put({'type':'info', 'message':'Resuming a paused process'})
                p = paused_process.pop()
                try:  # ensure does not fail if process terminated unexpectedly
                    psutil.Process(p.pid).resume()
                    event_queue.put({'type':'change my process', 'pid':p.pid, 'status':'processing'})
                    event_queue.put({'type':'log_file_only', 'message':'Resumed a paused process'})
                except:
                    pass
                  
            # try to create new process (no more processses are suspended)
            if dedicated_process.value > len(multiprocessing.active_children()):

                # check it has been a long time enough since last check of database with nothing to process
                if (datetime.datetime.now() - last_access_no_case).total_seconds() > config.db_connect_frequency:
                    event_queue.put({'type':'log_file_only', 'message':'Trying to get new cases from database'})
                    try_new_case = True  # we can try to get new case to process from database

                    while try_new_case:
                        refresh_status_daemon_process(alive_process, dedicated_process, event_queue, exit_program, gui_answer, paused_process)

                        # try to get a case that has a too long last_heartbeat
                        limit_last_heartbeat = datetime.datetime.now() - datetime.timedelta(seconds=config.db_heartbeat_dead)
                        case_to_process = mongodb.cases.find_and_modify(
                                query={"user_group":settings['user group'], 'instance':settings['instance'], "status":"processing", 'last_heartbeat':{'$lt':limit_last_heartbeat},"application":{"$in":possible_apps}},
                                sort= [("_id", pymongo.ASCENDING)],
                                fields= ['path', 'application', 'origin.user', 'origin.machine', 'processors.processor_list'],
                                update={"$set":{'last_heartbeat': datetime.datetime.now(), 'processors.time.start': datetime.datetime.now()},
                                    '$push':{'processors.processor_list': {'machine': platform.node(), 'user': getpass.getuser()}}})

                        if case_to_process is None:
                            # get a new case (returns original fields and not updated ones)
                            case_to_process = mongodb.cases.find_and_modify(
                                    query={"user_group":settings['user group'], 'instance':settings['instance'], "status":"to process", "application":{"$in":possible_apps}}, sort= [("_id", pymongo.ASCENDING)],
                                    fields= ['path', 'application', 'origin.user', 'origin.machine', 'processors.processor_list'],
                                    update={"$set":{'status': 'processing', 'last_heartbeat': datetime.datetime.now(), 'processors.time.start': datetime.datetime.now()},
                                        '$push':{'processors.processor_list': {'machine': platform.node(), 'user': getpass.getuser()}}})

                        refresh_status_daemon_process(alive_process, dedicated_process, event_queue, exit_program, gui_answer, paused_process)

                        if case_to_process is None:
                            # there is currently no case to run, try later
                            try_new_case = False
                            last_access_no_case = datetime.datetime.now()
                            event_queue.put({'type':'log_file_only', 'message':'No cases are currently available on database'})

                        else:
                            # check that case has not failed to process already 3 times
                            if len(case_to_process['processors']['processor_list']) >= 3:
                                event_queue.put({'type':'info', 'message':'A case from database has failed too many times'})
                                mongodb.cases.update({'_id':case_to_process['_id']},
                                                     {'$set': {'status': 'error: case failed to process already 3 times', 'processors.time.end': datetime.datetime.now()},
                                                     '$pop': {'processors.processor_list':1}})  # remove current processor from list since operation is cancelled

                            else:
                                # launch the case
                                new_process = multiprocessing.Process(target=launch_process, daemon = True,
                                                                     args=(case_to_process, event_queue, server_path, settings))
                                new_process.start()

                                # keep track of process for gui
                                event_queue.put({'type':'add my process', 'pid':new_process.pid, 'start':datetime.datetime.now(), 'application':case_to_process['application'],
                                                'originator': case_to_process['origin']['user'], 'status':'processing'})
                                alive_process.append({'_id':case_to_process['_id'], 'process':new_process, 'last heartbeat':datetime.datetime.now()})
                        
                            try_new_case = dedicated_process.value > len(multiprocessing.active_children())


def launch_process(case, event_queue, server_path, settings):
    '''Launch one process from database.

    Mongo database is updated when process finishes.
    
    Args:
        case: case to process obtained from mongo database.
        event_queue: queue of events to process by gui.
        server_path: path of file server as defined in "server.txt" file.
        settings: list of settings from settings.txt on file server.
    '''

    event_queue.put({'type':'log_file_only', 'message':'Launching case {}'.format(case['_id'])})
    case_server_path_absolute = server_path / case['path']
    if not case_server_path_absolute.is_file():
        if server_path.is_dir():  # check that server is still accessible
            # create new connection
            mongodb = pymongo.MongoClient("{}".format(settings['mongodb server'])).gridcompute
            mongodb.authenticate(settings['user group'], settings['password'])
            # mark file as not existing
            mongodb.cases.update({'_id':case['_id']}, {'$set': {'status': 'error: file input not found', 'processors.time.end': datetime.datetime.now()}})
            event_queue.put({'type':'info', 'message':'Error: File input for case {} not found at {}'.format(case['_id'], case['path'])})
        else:
            event_queue.put({'type':'critical', 'message':'Server not accessible at {}'.format(server_path)})
            raise SystemExit
    else:
        # Prepare temporary folder to run the case
        with tempfile.TemporaryDirectory() as temp_directory:
            event_queue.put({'type':'log_file_only', 'message':'Launching case {} in {}'.format(case['_id'], temp_directory)})
            case_path = str(pathlib.Path(temp_directory) / pathlib.Path(case['path']).name)
            shutil.copy(src = str(case_server_path_absolute), dst = case_path)
            # extract all files and remove zip file
            with zipfile.ZipFile(case_path) as zip_case:
                zip_case.extractall(temp_directory)
            os.remove(case_path)

            # list files and rename them as originally (without their position indicator)
            list_files = []  # list containing tuple (position, original file name)
            input_files_numbered = tuple(pathlib.Path(temp_directory).iterdir())
            for file in input_files_numbered:
                position, original_name = file.name.split('_', 1)
                original_file = pathlib.Path(temp_directory) / original_name
                file.rename(pathlib.Path(original_file))
                list_files.append((int(position), original_file))

            # list files as they were sent to server
            original_files_sorted = tuple(x[1].as_posix() for x in sorted(list_files))

            # Load module for processing the case
            try:
                process_module = return_module(case['application'], 'process')
            except:
                event_queue.put({'type':'error', 'message':'Error while importing "{}" process module\nProcess daemon exiting'.format(case['application'])})
                return
            
            # Process and return output files
            try:
                output_files = process_module.process_case(original_files_sorted)
            except:
                event_queue.put({'type':'error', 'message':'Error while executing "process_case" from "{}" process module'.format(case['application'])})
                return

            # zip all output files
            zip_output = str(pathlib.Path(temp_directory) / "output_files")
            with zipfile.ZipFile(zip_output, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_case:
                for output_number, output_file in enumerate(output_files):
                    # create zip file and add position of file in its name
                    if pathlib.Path(output_file).is_file(): # if this is a file, we just write it
                        zip_case.write(output_file, arcname = '{}_{}'.format(output_number, pathlib.Path(output_file).name))
                    elif pathlib.Path(output_file).is_dir(): # if this is a folder, we write full structure
                        if not tuple(pathlib.Path(output_file).iterdir()): # if folder empty, we just write empty folder
                            zif = zipfile.ZipInfo('{}_{}/'.format(output_number, pathlib.Path(output_file).name))
                            zip_case.writestr(zif, '')
                        else: # this is a folder with contents
                            empty_dirs = [] # we keep track of all the empty directories
                            for root, dirs, files in os.walk(output_file):
                                empty_dirs.extend([dir for dir in dirs if not tuple((pathlib.Path(root) / dir).iterdir())])
                                for name in files:
                                    full_path = pathlib.Path(root) / name
                                    archive_path = pathlib.Path('{}_{}'.format(output_number, pathlib.Path(output_file).name)) / full_path.relative_to(pathlib.Path(output_file))
                                    zip_case.write(str(full_path), arcname = str(archive_path))
                                for dir in empty_dirs:
                                    full_path = pathlib.Path(root) / dir
                                    archive_path = pathlib.Path('{}_{}/'.format(output_number, pathlib.Path(output_file).name)) / full_path.relative_to(pathlib.Path(output_file))
                                    zif = zipfile.ZipInfo('{}/'.format(archive_path))
                                    zip_case.writestr(zif, '')
                                empty_dirs = []

            # create folder structure if not existing: "Cases/user/machine/case"
            results_folder_relative_to_server = pathlib.Path('Results') / case['origin']['user'].upper() / case['origin']['machine'].upper()
            results_folder_absolute = server_path / results_folder_relative_to_server
            os.makedirs(str(results_folder_absolute), exist_ok = True)

            # copy case using unique identifier on file server
            result_path_relative_to_folder = results_folder_relative_to_server / pathlib.Path(case['path']).name
            result_path_absolute = server_path / result_path_relative_to_folder
            shutil.copy(src = zip_output, dst = str(result_path_absolute))

        # create new connection
        mongodb = pymongo.MongoClient("{}".format(settings['mongodb server'])).gridcompute
        mongodb.authenticate(settings['user group'], settings['password'])
        # mark case on database as processed
        mongodb.cases.update({'_id':case['_id']}, {'$set': {'status': 'processed', 'path': result_path_relative_to_folder.as_posix(), 'processors.time.end': datetime.datetime.now()}})

        # remove case from cases folder
        os.remove(str(case_server_path_absolute))

    event_queue.put({'type':'log_file_only', 'message':'Processed case {}'.format(case['_id'])})

def run_daemon_receive(applications_with_receive, event_queue, exit_program, server_path, settings):
    '''Run "daemon receive" that retrieve back cases from server after they have been processed.
    
    Daemon receive runs continuously and check on database if output files are available.
    
    Args:
        applications_with_receive: dictionary of applications that have a process function.
        event_queue: queue of events to process by gui.
        exit_program: variable scanned by daemons to know when to exit.
        server_path: path of file server as defined in "server.txt" file.
        settings: list of settings from settings.txt on file server.
    '''

    if not len(applications_with_receive):
        event_queue.put({'type':'info', 'message box':True, 'message':'Possible applications to receive calculations: None'})
        return
    possible_apps = list(applications_with_receive.keys())
    possible_apps.sort()
    event_queue.put({'type':'info', 'message':'Possible applications to receive calculations: {}'.format(possible_apps)})

    # create new connection
    mongodb = pymongo.MongoClient('{}'.format(settings['mongodb server'])).gridcompute
    mongodb.authenticate(settings['user group'], settings['password'])
    
    while True:
        check_quit_program(exit_program)

        case_to_receive = mongodb.cases.find_one({
            "user_group":settings['user group'], 'instance':settings['instance'], "status":"processed",
            'origin.user':getpass.getuser(), 'origin.machine':platform.node(),
            "application":{"$in":possible_apps}},
            fields= ['path', 'application', 'origin.user'])

        if case_to_receive is None:
            # there is currently no case to receive
            wait_remaining = config.db_connect_frequency
            check_quit_program(exit_program)
            while wait_remaining > 0:
                time.sleep(min(wait_remaining, config.daemon_pause))
                wait_remaining -= config.daemon_pause
                check_quit_program(exit_program)

        elif not (server_path / case_to_receive['path']).is_file():
            if server_path.is_dir():  # check that server is still accessible
                mongodb.cases.update({'_id':case_to_receive['_id']}, {'$set': {'status': 'error: file output not found', 'processors.time.end': datetime.datetime.now()}})
                event_queue.put({'type':'info', 'message':'Error: File onput for case {} not found at {}'.format(case_to_receive['_id'], case_to_receive['path'])})
            else:
                event_queue.put({'type':'critical', 'message':'Server not accessible at {}'.format(server_path)})
                raise SystemExit
        else:
            event_queue.put({'type':'log_file_only', 'message':'Receiving case {}'.format(case_to_receive['_id'])})
            event_queue.put({'type':'add my process', 'pid':os.getpid(), 'start':datetime.datetime.now(), 'application':case_to_receive['application'], 'originator': case_to_receive['origin']['user'], 'status':'receiving'})

            case_to_receive_absolute = server_path / case_to_receive['path']
            # Prepare temporary folder to receive the case
            with tempfile.TemporaryDirectory() as temp_directory:
                event_queue.put({'type':'log_file_only', 'message':'Processing request to receive case {} in {}'.format(case_to_receive['_id'], temp_directory)})
                case_path = str(pathlib.Path(temp_directory) / pathlib.Path(case_to_receive['path']).name)
                shutil.copy(src = str(case_to_receive_absolute), dst = case_path)
                # extract all files and remove zip file
                with zipfile.ZipFile(case_path) as zip_case:
                    zip_case.extractall(temp_directory)
                os.remove(case_path)

                # list files and rename them as originally (without their position indicator)
                list_files = [] # list containing tuple (position, original file name)
                output_files_numbered = tuple(pathlib.Path(temp_directory).iterdir())
                for file in output_files_numbered:
                    position, original_name = file.name.split('_', 1)
                    original_file = pathlib.Path(temp_directory) / original_name
                    file.rename(pathlib.Path(original_file))
                    list_files.append((int(position), original_file))

                # list files as they were sent to server
                original_files_sorted = tuple(x[1].as_posix() for x in sorted(list_files))

                # Load module for receiving the case
                try:
                    receive_module = return_module(case_to_receive['application'], 'receive')
                except:
                    event_queue.put({'type':'error', 'message':'Error while importing "{}" receive module\nReceive daemon exiting'.format(case_to_receive['application'])})
                    return

                # Execute receive function
                try:
                    receive_module.receive_case(original_files_sorted)
                except:
                    event_queue.put({'type':'error', 'message':'Error while executing "receive_case" from "{}" receive module\nReceive daemon about to exit'.format(case_to_receive['application'])})
                    return

            # mark case on database as received
            mongodb.cases.update({'_id':case_to_receive['_id']}, {'$set': {'status': 'received', 'path': '', 'origin.time.end': datetime.datetime.now()}})

            # remove case from results folder
            os.remove(str(case_to_receive_absolute))
            
            event_queue.put({'type':'log_file_only', 'message':'Received case {}'.format(case_to_receive['_id'])})
            event_queue.put({'type':'remove my process', 'pid':os.getpid()})


def return_module(application, function):
    ''' import app-specific function send, process or receive '''
    if function == "send":
        return importlib.import_module("{}.send".format(application))
    elif function == 'process':
        return importlib.import_module("{}.process".format(application))
    elif function == 'receive':
        return importlib.import_module("{}.receive".format(application))


if __name__ == "__main__":
    event_queue = multiprocessing.Queue()
    test_server = Server(event_queue)
