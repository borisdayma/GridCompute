'''This module contains all GUI functionalities.

It generates the main interface and handles any event that needs to be
communicated to the user.'''

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


import datetime
import multiprocessing
import os
import pathlib
import queue
import threading
import tkinter as tk
import tkinter.filedialog, tkinter.font, tkinter.messagebox, tkinter.scrolledtext
from tkinter import ttk

import g_config as config


class GUI:
    '''
    Class handling GridCompute interface.

    It contains every parameter and module required for GUI. At creation, it displays a progress bar.

    Args:
        root: main Tk instance
        application: application selected in gui
        app_combobox: widget associated with application
        cases_dict (dict): dictionary where key is the id of tree item and value
                  is the list of input files associated to the case
        cases_refresh_label: label identifying time of refresh of "my cases"
        cases_status_label: label identifying status of refresh of "my cases"
        dedicated_process: number of dedicated process selected in gui
        event_queue: queue of events to process by gui
        init_label, init_progress: elements used only at GridCompute start
        log: gui element associated to logging
        my_process_pid_id (dict): dictionary of pid to gui id for treeview in "my processes"
        progress_bar: progress bar in progress window
        progress_label: text present on progress window
        progress_window: top level window showing progress of current task
                       set to None if progress window not existing or closed
        server: Server instance containing main functionalities
        tree_cases: widget containing cases to submit
        tree_my_cases: widget containing "my cases"
        tree_my_process: widget containing "my processes"
    '''

    def __init__(self):

        # Create and name main window
        self.root = tk.Tk()
        self.root.title(config.title_windows)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Initialize gui variables
        self.application = tk.StringVar()
        self.app_combobox = None     # initialized in "populate" method
        self.cases_dict = dict()
        self.cases_refresh_label = tk.StringVar(value = 'status at\nn/a')
        self.cases_status_label = tk.StringVar(value = 'cases to process: n/a\ncases to receive: n/a')
        self.dedicated_process = tk.StringVar(value = 0)
        self.event_queue = multiprocessing.Queue()
        self.my_process_pid_id = dict()
        self.progress_bar = None     # initialized in "create_progress_window" method
        self.progress_label = None   # initialized in "create_progress_window" method
        self.progress_window = None  # initialized in "create_progress_window" method
        self.server = None           # initialized in "populate" method
        self.tree_cases = None       # initialized in "populate" method
        self.tree_my_cases = None    # initialized in "populate" method
        self.tree_my_process = None  # initialized in "populate" method

        # Create and grid the outer content frame
        self.main_frame = ttk.Frame(self.root, padding=8)
        self.main_frame.grid(column=0, row=0, sticky=(tk.N,tk.W,tk.E,tk.S))

        # Create log interface (without display) to start logging in it
        self.log_frame = ttk.Frame(self.main_frame, padding=4, borderwidth=1, relief = "raised")
        self.log = tk.scrolledtext.ScrolledText(
                self.log_frame, width=1, height=1, font=tk.font.nametofont("TkDefaultFont"), wrap="word",
                state="disabled")

        # Create loading interface
        self.init_label = ttk.Label(self.main_frame, text = "Initializing")
        self.init_label.grid(column=0, row=0)
        self.init_progress = ttk.Progressbar(self.main_frame, orient=tk.HORIZONTAL, length=180, mode='indeterminate')
        self.init_progress.grid(column=0, row=1)
        self.init_progress.start()

        # Assign exit function
        self.root.protocol('WM_DELETE_WINDOW', self.exit_program)

        # Modify standard styles
        s = ttk.Style()
        s.configure('TButton', justify='center')

        self.event_queue.put({'type':'log_file_only', 'message':'Initialized gui'})

        self.root.after(config.gui_refresh_interval, self.refresh)  # launch refresh of GUI

    def link_server(self, server):
        '''Associate GUI to a Server instance.
        
        Args:
            server: Server instance.'''

        self.server = server
        
    def populate(self):
        '''Populate GUI during loading of program.'''

        # Delete initialization widgets
        self.init_label.destroy()
        self.init_progress.destroy()

        # Set up resize parameters
        self.main_frame.columnconfigure(0, weight=0)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=0)
        self.main_frame.rowconfigure(1, weight=2, uniform=1)
        self.main_frame.rowconfigure(2, weight=1, uniform=1)
        self.root.minsize(800,600)

        # Create layout for number of processes
        frame_process_used = ttk.Labelframe(self.main_frame, text='My Processes')
        frame_process_used.grid(column=2, row=0)
        label_txt_process = ttk.Label(frame_process_used, text = "dedicated to the grid")
        label_txt_process.grid(column=1, row=0, padx=(0,3), pady=3)
        spinbox_process_used = tk.Spinbox(
                frame_process_used, from_=0.0, to=config.max_number_process, textvariable=self.dedicated_process,
                width = 3, justify = "center", state="readonly", readonlybackground="")
        spinbox_process_used.grid(column=0, row=0, padx=3, pady=3)

        # Display grid name based on user group
        label_client_grid = ttk.Label(self.main_frame, text="Grid\n{} {}".format(self.server.settings['user group'], self.server.settings['instance']), justify="center")
        label_client_grid.grid(column=1, row=0)

        # Display logo
        label_logo = ttk.Label(self.main_frame, text="LOGO\nTO CREATE", justify='center')
        label_logo.grid(column=0, row=0)
       
        # Logging interface
        self.log_frame.grid(column=0, row=2, columnspan=3, sticky=(tk.N,tk.W,tk.E,tk.S))
        label_log = ttk.Label(self.log_frame, text="log")
        label_log.grid(column=0, row=0, pady=(0,2))
        self.log.grid(column=0, row=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=0)
        self.log_frame.rowconfigure(1, weight=1)

        # Create the notebook
        notebook = ttk.Notebook(self.main_frame)
        send_cases_frame = ttk.Frame(notebook, padding=4)
        my_cases_frame = ttk.Frame(notebook, padding=4)
        my_process_frame = ttk.Frame(notebook, padding=4)
        notebook.add(send_cases_frame, text='send cases')
        notebook.add(my_cases_frame, text='my cases')
        notebook.add(my_process_frame, text='my processes')
        notebook.grid(column=0, row=1, columnspan=3, sticky=(tk.N, tk.S, tk.E, tk.W), pady=8)

        # Create the "send cases" frame
        app_frame = ttk.Frame(send_cases_frame, padding=4, borderwidth=1, relief = "sunken")
        app_frame.grid(column=0, row=0, rowspan=2, sticky=(tk.N,tk.W,tk.E,tk.S), padx=(0,10))
        app_label = ttk.Label(app_frame, text="Application")
        app_label.grid(column=0, row=0,pady=(0,4))
        self.app_combobox = ttk.Combobox(
                app_frame, textvariable=self.application, width=20,
                values=tuple(sorted(self.server.applications_with_send().keys())), justify="center", state="readonly")
        self.app_combobox.grid(column=0, row=1, sticky=(tk.N,tk.W,tk.E,tk.S))
        add_cases_button=ttk.Button(send_cases_frame, text='add cases', command=self.add_cases)
        add_cases_button.grid(column=1,row=0, sticky=(tk.N,tk.W,tk.E,tk.S), pady=(0,4))
        remove_selected_button=ttk.Button(send_cases_frame, text='remove selected', command=self.remove_selected)
        remove_selected_button.grid(column=1,row=1, sticky=(tk.N,tk.W,tk.E,tk.S))
        submit_list_button=ttk.Button(send_cases_frame, text='submit list\nto server', command=self.submit_to_server)
        submit_list_button.grid(column=2,row=0, rowspan=2, sticky=(tk.N,tk.W,tk.E,tk.S), padx=(10,0))
        send_cases_frame.rowconfigure(2, weight=1)
        send_cases_frame.columnconfigure(0, weight=1)
        app_frame.columnconfigure(0, weight=1)

        # Create the tree for list of cases to send
        tree_cases_frame = ttk.Frame(send_cases_frame)
        tree_cases_frame.grid(row=2, column=0, columnspan=3, pady=(8,0), sticky=(tk.N,tk.W,tk.E,tk.S))
        self.tree_cases = ttk.Treeview(tree_cases_frame, columns=("status",))
        self.tree_cases.column("#0", minwidth=80, anchor="center")
        self.tree_cases.column("status", width=80, minwidth=80, stretch=tk.NO, anchor="center")
        self.tree_cases.heading("#0", text="Case")
        self.tree_cases.heading("status", text="Status")
        self.tree_cases.grid(row=0, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        scroll_cases = ttk.Scrollbar(tree_cases_frame, orient=tk.VERTICAL, command=self.tree_cases.yview)
        scroll_cases.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree_cases['yscrollcommand'] = scroll_cases.set
        tree_cases_frame.rowconfigure(0, weight=1)
        tree_cases_frame.columnconfigure(0, weight=1)

        # Create the "my cases" frame
        status_frame = ttk.Frame(my_cases_frame, padding=4, borderwidth=1, relief = "sunken")
        status_frame.grid(column=0, row=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        cases_status_label = ttk.Label(status_frame, textvariable=self.cases_status_label)
        cases_status_label.grid(column=2, row=0)
        refresh_button=ttk.Button(status_frame, text='refresh now', command=self.refresh_my_cases)
        refresh_button.grid(column=0,row=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        refresh_label = ttk.Label(status_frame, textvariable=self.cases_refresh_label)
        refresh_label.grid(column=1, row=0, padx=60)
        my_cases_frame.columnconfigure(0, weight=1)
        my_cases_frame.rowconfigure(1, weight=1)
        status_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=1)
        status_frame.columnconfigure(2, weight=1)

        # Create the tree for my cases status
        tree_my_cases_frame = ttk.Frame(my_cases_frame)
        tree_my_cases_frame.grid(row=1, column=0, pady=(6,0), sticky=(tk.N,tk.W,tk.E,tk.S))
        cases_server_label = ttk.Label(tree_my_cases_frame, text='Cases on Server')
        cases_server_label.grid(column=0, row=0)
        self.tree_my_cases = ttk.Treeview(tree_my_cases_frame, columns=('application', 'processor', 'status'))
        self.tree_my_cases.column("#0", minwidth=80, anchor="center")
        self.tree_my_cases.column("application", width=120, minwidth=120, stretch=tk.NO, anchor="center")
        self.tree_my_cases.column("processor", width=80, minwidth=80, stretch=tk.NO, anchor="center")
        self.tree_my_cases.column("status", width=80, minwidth=80, stretch=tk.NO, anchor="center")
        self.tree_my_cases.heading("#0", text="Case")
        self.tree_my_cases.heading("application", text="Application")
        self.tree_my_cases.heading("processor", text="Processor")
        self.tree_my_cases.heading("status", text="Status")
        self.tree_my_cases.grid(row=1, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        scroll_cases = ttk.Scrollbar(tree_my_cases_frame, orient=tk.VERTICAL, command=self.tree_my_cases.yview)
        scroll_cases.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.tree_my_cases['yscrollcommand'] = scroll_cases.set
        tree_my_cases_frame.rowconfigure(1, weight=1)
        tree_my_cases_frame.columnconfigure(0, weight=1)

        # Create the tree for my processes
        tree_my_process_frame = ttk.Frame(my_process_frame)
        tree_my_process_frame.grid(row=0, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.tree_my_process = ttk.Treeview(tree_my_process_frame, columns=('originator', 'start', 'status'))
        self.tree_my_process.column("#0", minwidth=120, anchor="center")
        self.tree_my_process.column("originator", width=120, minwidth=120, anchor="center")
        self.tree_my_process.column("start", width=120, minwidth=120, stretch=tk.NO, anchor="center")
        self.tree_my_process.column("status", width=120, minwidth=120, stretch=tk.NO, anchor="center")
        self.tree_my_process.heading("#0", text="Application")
        self.tree_my_process.heading("originator", text="Originator")
        self.tree_my_process.heading("start", text="Start")
        self.tree_my_process.heading("status", text="Status")
        self.tree_my_process.grid(row=0, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        scroll_cases = ttk.Scrollbar(tree_my_process_frame, orient=tk.VERTICAL, command=self.tree_my_process.yview)
        scroll_cases.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree_my_process['yscrollcommand'] = scroll_cases.set
        my_process_frame.columnconfigure(0, weight=1)
        my_process_frame.rowconfigure(0, weight=1)
        tree_my_process_frame.rowconfigure(0, weight=1)
        tree_my_process_frame.columnconfigure(0, weight=1)

        # Create menus
        self.root.option_add('*tearOff', tk.FALSE)   # for Tk backwards compatibility
        menubar = tk.Menu(self.root)
        self.root['menu'] = menubar
        menu_file = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_file, label='File')
        menu_file.add_command(label='Exit', command=self.exit_program)
        menu_tools = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_tools, label='Tools')
        menu_tools.add_command(label='Create report of database', command=self.create_report)
        menu_help = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_help, label='Help')
        menu_help.add_command(label='Help', command=self.open_help)
        menu_help.add_command(label='License', command=self.open_license)
        menu_help.add_command(label='About', command=self.open_about)

        self.event_queue.put({'type':'log_file_only', 'message':'Populated gui'})

    def refresh(self):
        '''Refresh GUI at regular intervals.'''

        try:
            while True:
                self.handle_next_event()
        except queue.Empty:
            pass

        # reschedule process to refresh interface
        self.root.after(config.gui_refresh_interval, self.refresh)

    def exit_program(self):
        '''Communicate to processes to exit program.'''

        if self.askokcancel('Do you really wish to quit?'):
            self.event_queue.put({'type':'log_file_only', 'message':'User asked to exit application'})
            self.create_progress_window(progress_mode='indeterminate', progress_text='closing all processes')
            threading.Thread(target=self.server.exit_processes).start()

    def create_progress_window(self, progress_mode, progress_text, progress_max = 100):
        '''
        Create a progress window.

        The progress window can be controlled afterwards through the event_queue parameter.
        Refer to function "handle_next_event".

        Args:
            progress_mode (str): "determinate" if progress level evolution needs to be controlled or "indeterminate".
            progress_text (str): text displayed initially on the progress window.
            progress_max (int): argument equal to maximal progress value when complete.
        '''

        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title(config.title_windows)
        frame = ttk.Frame(self.progress_window, padding=8)
        frame.grid(column=0, row=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.progress_label = ttk.Label(frame, text = progress_text)
        self.progress_label.grid(column=0, row=0)
        self.progress_bar = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=180,
                                           mode=progress_mode, maximum=progress_max, value=0)
        self.progress_bar.grid(column=0, row=1)
        if progress_mode == 'indeterminate':
            self.progress_bar.start()

    def error(self, msg):
        '''Display error on screen.
        
        Args:
            msg (str): Message to be displayed.'''

        tk.messagebox.showerror(title = config.title_windows, message = msg, parent = self.root)

    def warning(self, msg):
        '''Display warning on screen
        
        Args:
            msg (str): Message to be displayed.'''

        tk.messagebox.showwarning(title = config.title_windows, message = msg, parent = self.root)

    def info(self, msg):
        '''Display info on screen
        
        Args:
            msg (str): Message to be displayed.'''

        tk.messagebox.showinfo(title = config.title_windows, message = msg, parent = self.root)

    def askokcancel(self, msg):
        '''Ask a question to user.
        
        Args:
            msg (str): Message to be displayed.

        Returns:
            bool: True if user enters "ok", False otherwise.
        '''

        return tkinter.messagebox.askokcancel(title = config.title_windows, message = msg, parent = self.root)
        
    def add_cases(self):
        '''Display a window to select cases to submit to server and adds them on the list.'''

        # check a task is not already running
        if self.progress_window:
            return

        # check that an application is selected
        if not self.application.get():
            self.error("You must first select an application")
            return

        files_selected = tk.filedialog.askopenfilenames(parent = self.root)
        if files_selected != "":
            self.event_queue.put({'type':'log_file_only', 'message':'User adds cases to send'})
            self.create_progress_window(progress_mode = 'determinate', progress_text = 'preparing to add cases',
                                  progress_max = len(files_selected))

            # execute function in a thread to avoid blocking GUI
            threading.Thread(target=self.server.add_cases, daemon=True,
                            args=(files_selected, self.application.get(), self.progress_window)).start()

    def create_report(self):
        '''Create a full report from database containing all cases from same "user group".
        Ask user where he wants to save the report.'''

        # check a task is not already running
        if self.progress_window:
            return

        file_report = tk.filedialog.asksaveasfilename(parent = self.root, filetypes = [('Text file', '.txt')])
        if file_report == "":
            return

        self.event_queue.put({'type':'log_file_only', 'message':'User requests to generate a report of database'})
        self.create_progress_window(progress_mode = 'determinate',
                              progress_text = 'accessing database')  # progress_max taken from database later

        # execute function in a thread to avoid blocking GUI
        threading.Thread(target=self.server.create_report, daemon=True,
                        args=(file_report, self.progress_window)).start()

    def remove_selected(self):
        '''Removes selected cases to submit from the list.'''

        self.event_queue.put({'type':'log_file_only', 'message':'User requests to remove cases from "send cases" tab'})
        
        for item in self.tree_cases.selection():
            self.tree_cases.delete(item)
            del self.cases_dict[item]

        # allow changing app if list is empty
        if not len(self.tree_cases.get_children()):
            self.app_combobox['state'] = 'readonly'

    def submit_to_server(self):
        '''Send all cases (not yet submitted) from the list to the server.'''

        # check a task is not already running
        if self.progress_window:
            return

        # check that there are cases to submit
        if 'ready' not in map(lambda x: self.tree_cases.set(x, 'status'), self.tree_cases.get_children()):
            self.warning('You have no cases to submit')
            return

        # user to confirm submission of cases
        if not self.askokcancel('All "ready" cases from the list are going to be submitted to server'):
            return

        self.event_queue.put({'type':'log_file_only', 'message':'User confirms to submit cases to server'})

        # keep track of list of cases to submit
        cases_to_submit = [(case, self.cases_dict[case])
                          for case in self.tree_cases.get_children()
                          if self.tree_cases.set(case, 'status') == 'ready']

        self.create_progress_window(progress_mode = 'determinate', progress_text = 'preparing to submit cases',
                              progress_max = len(cases_to_submit))

        # execute function in a thread to avoid blocking GUI
        threading.Thread(target=self.server.submit_to_server, daemon=True,
                        args=(cases_to_submit, self.application.get(), self.progress_window)).start()

    def open_help(self):
        '''Display a help message.'''
        self.info('For more information, please consult the documentation at\ngridcompute.readthedocs.org')

    def open_about(self):
        '''Display program information.'''
        self.info('{} version {}\n{}'.format(config.program_name, config.version, config.copyright))

    def open_license(self):
        '''Display licenses used by the program.'''

        # Display all licenses
        license_window = tk.Toplevel(self.root)
        license_window.title(config.title_windows)
        main_frame = ttk.Frame(license_window, padding=8)
        main_frame.grid(column=0, row=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        license_label = ttk.Label(main_frame, text = "Licenses")
        license_label.grid(column=0, row=0, pady=(0,2))
        license_text = tk.scrolledtext.ScrolledText(main_frame, width=1, height=1, font=tk.font.nametofont("TkDefaultFont"), wrap="word", state="normal")
        license_text.grid(column=0, row=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        license_window.columnconfigure(0, weight=1)
        license_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        license_window.minsize(500,400)

        # Display main license
        main_license_file = pathlib.Path('licenses') / 'GridCompute.txt'
        with main_license_file.open() as f:
            main_license = f.read()
        license_text.insert('end', '{}\n\n{}'.format(config.program_name.upper(), main_license))

        # Show other licenses 
        for license_file in pathlib.Path('licenses').iterdir():
            if 'GridCompute' not in str(license_file):
                with license_file.open(encoding='utf8') as f:
                    license = f.read()
                    license_text.insert('end', '\n\n{}\n\n{}\n\n{}'.format('*'*75, license_file.stem.upper(), license))

        license_text['state']='disabled'

    def refresh_my_cases(self):
        '''Refresh the list of "my cases".
        
        Access database and display details of user cases that have not been received yet.'''

        # check a task is not already running
        if self.progress_window:
            return

        self.event_queue.put({'type':'log_file_only', 'message':'User requests to refresh "my cases" tab'})

        self.create_progress_window(progress_mode = 'indeterminate', progress_text = 'retrieving cases from server')

        # refresh "my cases" tab
        item_list = self.tree_my_cases.get_children()
        if len(item_list):
            self.tree_my_cases.delete(*item_list)
        self.cases_status_label.set('cases to process: 0\ncases to receive: 0')
        self.cases_refresh_label.set('status at\n{}'.format(datetime.datetime.now().strftime('%X')))

        # execute function in a thread to avoid blocking GUI
        threading.Thread(target=self.server.refresh_my_cases, daemon=True,
                        args=(self.progress_window,)).start()

    def handle_next_event(self):
        '''      
        Handles the next event from communicated to the GUI through event_queue variable.
        
        Each element in event_queue is a dictionary. Action performed depends on value of *type* key:
    
            - log_file_only: log a message in the log file, no display in gui
            - warning: display a warning
            - info: display an information in gui, optionally creating an info box
            - error: display an error
            - critical: display an error and exit program
            - change progress max: change value of progress window corresponding to completion
            - change progress: modify progress bar level and text
            - close progress: close progress window
            - add case: add a case in "send cases" tab
            - submitted case: show a case as submitted
            - terminate process?: ask user if he wants to terminate all processes
            -                  send answer through the connection pipe to daemon process
            - add my case: add a case in "my cases" tab
            - add my process: add a process in "my processes" tab
            - remove my process: remove a process from "my processes" tab
            - change my process: change the status of a process in "my processes" tab
            - populate: GUI can be fully populated
            - exit: close main window

        Raises:
            queue.empty: event_queue is empty, there are no more events to process.
        '''

        action = self.event_queue.get_nowait()
        write_log('handling event type: {}'.format(action['type']))

        if action['type'] == 'log_file_only':
            write_log(action['message'], gui_log = False)

        elif action['type'] == 'warning':
            write_log('Warning: {}'.format(action['message']), gui_log = self.log)
            self.warning(action['message'])

        elif action['type'] == 'info':
            write_log('Info: {}'.format(action['message']), gui_log = self.log)
            if 'message box' in action and action['message box'] == True:
                self.info(action['message'])

        elif action['type'] == 'error':
            write_log('Error: {}'.format(action['message']), gui_log = self.log)
            self.error(action['message'])

        elif action['type'] == 'critical':
            write_log('Critical Error: {}'.format(action['message']), gui_log = self.log)
            self.error(action['message'])
            raise SystemExit(action['message'])

        elif action['type'] == 'change progress max':
            if self.progress_window:
                self.progress_bar['maximum'] = action['progress maximum']

        elif action['type'] == 'change progress':
            if self.progress_window:
                self.progress_bar['value'] += action['progress increment']
                self.progress_label['text'] = action['progress label']

        elif action['type'] == 'close progress':
            if self.progress_window:
                self.progress_window.destroy()
                self.progress_window = None

        elif action['type'] == 'add case':
            new_case = action['case']
            id_gui = self.tree_cases.insert(
                    '', 'end', text=str(pathlib.Path(new_case[0])),  # path representation OS-specific
                    values=('ready'))
            self.cases_dict[id_gui] = new_case
            self.app_combobox['state'] = 'disabled'  # prevent from changing app

        elif action['type'] == 'submitted case':
            id_gui = action['case']
            self.tree_cases.set(id_gui, 'status', 'submitted')

        elif action['type'] == 'terminate process?':
            if not self.askokcancel('All running processes are going to be terminated'):
                self.dedicated_process.set(1)
            self.server.gui_answer.set()

        elif action['type'] == 'add my case':
            id_gui = self.tree_my_cases.insert(
                    '', 'end', text=str(pathlib.Path(action['case']))) # path representation OS-specific
            self.tree_my_cases.set(id_gui, 'application', action['application'])
            self.tree_my_cases.set(id_gui, 'processor', action['processor'])
            self.tree_my_cases.set(id_gui, 'status', action['status'])
            self.cases_status_label.set('cases to process: {}\ncases to receive: {}'.format(
                    action['cases to process'], action['cases to receive']))

        elif action['type'] == 'add my process':
            id_gui = self.tree_my_process.insert('', 'end', text=action['application'])
            self.tree_my_process.set(id_gui, 'originator', action['originator'])
            self.tree_my_process.set(id_gui, 'start', action['start'].strftime('%X'))
            self.tree_my_process.set(id_gui, 'status', action['status'])
            self.my_process_pid_id[action['pid']] = id_gui  # map pid to gui id

        elif action['type'] == 'remove my process':
            id_gui = self.my_process_pid_id[action['pid']]
            self.tree_my_process.delete(id_gui)
            del self.my_process_pid_id[action['pid']]

        elif action['type'] == 'change my process':
            id_gui = self.my_process_pid_id[action['pid']]
            self.tree_my_process.set(id_gui, 'status', action['status'])

        elif action['type'] == 'populate':
            self.populate()

        elif action['type'] == 'exit':
            self.root.destroy()

        else:
            self.event_queue.put({'type':'error',
                                 'message':'"type" value not recognized in "event_queue": {}'.format(action['type'])})

def init_log():
    '''
    Initialize logging in file.
    
    Create necessary directory structure and remove previous log file.'''
    
    try:
        os.remove(str(config.log_path))
    except OSError:
        pass
    os.makedirs(str(config.log_path.parent), exist_ok = True)

def write_log(log_message, gui_log = None):
    '''
    Write log messages in log file and in GUI.
    
    Args:
        log_message: message to be displayed.
        gui_log: widget receiving log message.
               None if message not to be displayed in gui.
    '''

    time = datetime.datetime.now()
    log_text = '{} - {}'.format(time.strftime('%X'), log_message)
    with open(str(config.log_path), "a") as log_file:
        print(log_text, file = log_file)

    if gui_log:
        gui_log['state']='normal'
        gui_log.insert('end', '{}\n'.format(log_text))
        gui_log['state']='disabled'
