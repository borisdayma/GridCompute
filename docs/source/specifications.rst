.. include:: global.rst

Specifications
==============
 

Detailed workflow
*****************

The sequence of events is represented with numbered arrows herebelow:

|detailed workflow|

Architecture of shared folder
*****************************

In the same folder as main script or program, there is a file named "server.txt" which contains only the network path of main shared folder between all users used by GridCompute (folder that contains "Settings", "Cases" and "Results"). Ex: ``\\Server010\\Folder\\GridCompute``.

This shared folder has following architecture:

- *Settings* folder (to be at least read-only for users, read-write for administrators)

  .. _software_per_machine_specs:

  - Software_Per_Machine.csv: This file contains machine names and corresponding applications installed (using unique ID per application). The program looks for the *1* in the matrix.

      Ex::

        Machine name,Software 1,Software 2,Software 3
        Machine 1,1,1,1
        Machine 2,0,1,0
        Machine 3,0,0,0

    .. note:: This file is only used to detect what machine can run *process* functions. All machines can submit or receive cases.

  .. _settings_specs:

  - settings.txt: contains parameters of database on each line under the form: ``parameter name: value``. Parameters to define are the following:

    - mongodb server: address of the mongo instance including connection port containing gridcompute database

        Ex: ``mongodbserver.com:888`` or ``10.0.0.1:888`` or ``Machine123:888``

    - user group: Login used to connect on mongo database.
    - password: Password used to connect on mongo database.
    - instance: Data instance to consider. Example: ``0`` or ``debug``.

  - *Applications* folder

    - One file per application with unique ID (ex: *Software 1*).
      
      .. warning:: The folder name cannot contain a dot.

      It contains:

      - send.py: Defines how to select input and send calculations.
      - process.py: Will run when analysis are executed based on input received and will create output files.
      - receive.py: Will run when output files are present on server.

      More details are provided in `Application-specific scripts`_.


- *Cases* folder: Contains one folder per user and inside, one folder per machine (so that user can see easily his files) storing each case  as a zip file that has all input files/folders required.

- *Results* folder: Contains one folder per user and inside, one folder per machine storing each result as a zip file that has all output files/folders required.

.. note:: A template folder is present in source code in *template* folder and can be used to set up the shared folder.


Architecture of Mongo Database
******************************

GridCompute communicates with a mongo database that contains all the details on cases. Following entries are present:

- collection *cases*

  * _id: Unique Object Id based on timestamp of the case.
  * user_group: User group. Ex: ``ENGINEERING DEPARTMENT``.
  * instance: Instance used to isolate grids. Ex: ``0`` or ``debug``.
  * status: Current status of the case. It can be ``to process``, ``processing``, ``processed`` or ``received``.
  * last_heartbeat: Timestamp of last heartbeat sent to notify the database that the process is still alive.
  * application: Application associated to the case.
  * path: Path on file server refering to input/output case.
  * origin: Machine/User who submitted the case to the database.

    - machine
    - user
    - time

      * start: Time the case has been submitted to server.
      * end: Time the results have been retrieved from server.

  * processors

    - processor_list: List of Machine/Users who tried to process the case  (some attempts to process may have failed).

      * machine
      * user

    - time (start and end) for the last attempt to process

      * start: Time of the last attempt to process.
      * end: Time the process returned.

- collection *versions* (optional)

  * _id: Versions of program recognized by database.
  * status: Can be either ``allowed``, ``warning`` or ``refused``.
  * message: Message to be displayed when status is not ``allowed``.


Application-specific scripts
****************************

Applications can easily take advantage of distributed computing by creating 3 scripts, as detailed in following sections.

.. note:: Some examples are present in *template/Shared_Folder/Settings/Applications*.


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


Main code layout
****************

For details on *GridCompute* source code layout,  refer to :doc:`code`.


