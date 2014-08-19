.. include:: global.rst

Specifications
==============


Detailed workflow
*****************

The sequence of events is represented with numbered arrows herebelow:

|detailed workflow|

Architecture of shared folder
*****************************

In the same folder as main script or program, there is a file named "server.txt" which contains only the network path of main shared folder between all users used by GridCompute (folder that contains "Settings", "Cases" and "Results").
  Ex: "\\\\Server010\\Folder\\GridCompute"

This shared folder has following architecture:

- *Settings* folder (to be at least read-only for users, read-write for administrators)

  .. _software_per_machine_specs:

  - Software_Per_Machine.csv: This file contains machine names and corresponding applications installed (using unique ID per application). The program looks for the *1* in the matrix.

      Ex::

        Machine name,Software 1,Software 2,Software 3
        Machine 1,1,1,1
        Machine 2,0,1,0
        Machine 3,0,0,0

    .. note:: This file is only used to evaluate what machine can run *process* functions. All machines can submit or receive cases.

  .. _settings_specs:

  - settings.txt: contains parameters of database on each line under the form: "parameter name: value". Parameters to define are the following:

    - mongodb server: address of the mongo instance including connection port containing gridcompute database
        Ex:  'mongodbserver.com:888' or '10.0.0.1:888' or 'Machine123:888'
    - user group: login used to connect on mongo database
    - password: password used to connect on mongo database
    - instance: data instance to consider. Example: "0" or "debug"

  - *Applications* folder

    - One file per application with unique ID (ex: *Software 1*).
      Note: the folder name cannot contain a dot.
      It contains:

      - send.py: defines how to select input and send calculations
      - process.py: function will run when analysis are executed based on input received and will create output files
      - receive.py: function will run when output files are present on server

- *Cases* folder: Contains one folder per user and inside, one folder per machine (so that user can see easily his files) storing each case study as a zip file containing all files/folders required

- *Results* folder: Contains one folder per user and inside, one folder per machine storing each result as a zip file containing all files/folders required


Architecture of Mongo Database
******************************

GridCompute communicates with a mongo database that contains all the details on cases. Following entries are present:

- collection *cases*

  * _id: unique Object Id based on timestamp of the case
  * user_group: example "ENGINEERING DEPARTMENT"
  * instance: example "0" or "debug"
  * status: "to process", "processing", "processed", "received"
  * last_heartbeat: heartbeat are sent on running process to notify database that they are still alive
  * application: application associated to the case
  * path: path location of case
  * origin

    - machine
    - user
    - time

      * start: time case has been submitted to server
      * end: time results have been retrieved from server

  * processors

    - processor_list: list of processors (if some attempts to process failed)

      * machine
      * user

    - time (start and end) for the last attempt to process

- collection *versions* (optional)

  * _id: versions of program recognized by database
  * status: "allowed", "warning" or "refused"
  * message: message to be displayed when status is not "allowed"


Application-specific scripts
****************************

Applications can easily take advantage of distributed computing by creating 3 scripts, as detailed in following sections.

- receive.py: this script is executed in a temporary folder. Its input is the (ordered) list of output files returned in “process.py” script. At the end of execution, the temporary folder is deleted.

Some examples are present in *template/Shared_Folder/Settings/Applications*.


send.py
-------

.. automodule:: send
   :members:

process.py
----------

.. automodule:: process
   :members:

receive.py
----------

.. automodule:: receive
   :members:


Code layout
***********

The source code of *GridCompute* is split into a few modules.


main.py
-------

.. automodule:: main
   :members:

g_config.py
-----------

.. automodule:: g_config
   :members:

g_interface.py
--------------

.. automodule:: g_interface
   :members:

g_server_management.py
----------------------

.. automodule:: g_server_management
   :members:

database_management.py
----------------------

.. automodule:: database_management
   :members:

setup.py
--------
.. automodule:: setup
   :members:

TODO: Talk about server_template. 

TODO: This section needs to be completed by including source code documentation with autodoc.
