Tutorial
========

.. note:: This section only intends to give a quick presentation of GridCompute through the
          use of a (not very useful) demo application *Random Counter*. This application takes a file as input,
          performs a countdown from a random number, and returns the time needed for that countdown, along with
          the name of the input file. This output is then added to a file in the home directory of the person
          who requested the process.


Create GridCompute database
***************************

GridCompute requires a `MongoDB <http://www.mongodb.org/>`_ server to store all cases related information.


Create a MongoDB server
-----------------------

In this section, we are going to detail two possible scenarios: using a private server or using a specialized host.


Option 1: Create a private MongoDB server
+++++++++++++++++++++++++++++++++++++++++

In this example, we are going to assume that you want to use a `Ubuntu server <http://www.ubuntu.com/server>`_ in a virtual machine created with `VirtualBox <https://www.virtualbox.org/>`_. You can adapt it to install on a different OS and use of a virtual machine is only optional.

#. Install `VirtualBox <https://www.virtualbox.org/>`_.

#. Create a virtual machine in VirtualBox with at least 512MB RAM and 8Go drive.

#. Install `Ubuntu server <http://www.ubuntu.com/server>`_. **Activate option "Open-SSH Server" during installation** for convenient access to your server.

#. Set up port forwarding in VirtualBox:
   
   * host=22 (or 2222 for Ubuntu host), guest=22 if you want to access to your machine by ssh
   * host=27017, guest=27017 for access to Mongo database

#. From host, connect to guest through ssh.
     | On Ubuntu: ``ssh -p 2222 GUEST_USERNAME@HOST_MACHINE_NAME``
     | On Windows: you can use a program such as `putty <http://www.chiark.greenend.org.uk/~sgtatham/putty/>`_

#. Update Ubuntu packages and reboot.

   >>> sudo apt-get update
   >>> sudo apt-get upgrade
   >>> sudo sudo reboot

#. Install MongoDB per `instructions from MongoDB tutorial <http://docs.mongodb.org/manual/tutorial/install-mongodb-on-ubuntu/>`_.

#. In file */etc/mongod.conf*, commant line *bindip [...]*

#. Run ``sudo service mongod start``

#. Create a new database called *gridcompute*

   >>> mongo
   >>> use gridcompute

#. Add the user you will use from *gridcompute*. For example, for user *Group1* with password *gridcompute*:

   >>> db.createUser({user:"Group1", pwd:"gridcompute", roles:["readWrite"]})
   >>> quit()

#. `Set up MongoDB server`_


Option 2: Use a specialized host
++++++++++++++++++++++++++++++++

MongDB server instance can be hosted by a specialized website such as `Compose <https://www.compose.io/mongodb/>`_ or `Mongolab <https://mongolab.com/>`_.

#. Register to the host of your choice.

#. Create a new database **named "gridcompute"**.

#. Add the user you will use from *gridcompute*. For example, user *Group1* with password *gridcompute*.

#. `Set up MongoDB server`_


Set up MongoDB server
---------------------

The main purpose is only to define what version of gridcompute can work with the database.

.. note:: This section is optional. If you don't set up the database, a warning message will appear to notify you that the program version is not controlled by the server but the program will still work.

#. Open script *source/admin/database_management.py*

#. Edit the variables under ``if __name__ == "__main__"``

#. Run the script with **python 3**


Set-up of GridCompute
*********************

Before starting the program, you should follow these steps:

#. Download `latest version of GridCompute binary <https://github.com/borisd13/GridCompute/releases>`_. Choose the version associated to your OS.
#. Create a shared folder accessible (read and write) to every person that will use the program
#. Copy folder *template/Shared_Folder* from `source code <https://github.com/borisd13/GridCompute>`_ to the shared folder you are going to use with *GridCompute*.
#. At the root folder of *GridCompute* executable, there should be a file *server.txt*. Open it and copy the path to *GridCompute* shared folder (*Shared_Folder* path if you used the template).
#. Edit *settings.txt* from the template folder with your applicable parameters (refer to :ref:`settings.txt specifications <settings_specs>`)
#. Edit *Software_Per_Machine.csv* from the template folder (for more details refer to :ref:`Software_Per_Machine.csv specifications <software_per_machine_specs>`):

  - Add the name of your machine in the first column
  - Enter *1* for application *Random Counter* on the row corresponding to your machine name
  - Save as csv


Test GridCompute
****************

The following section will give you a brief overview of the program.

#. Run *GridCompute* executable. You will see the main window of the program.
#. Check at the bottom of the application that you can run *Random_Counter* as selected in *Software_Per_Machine.csv*.
#. Click on the application checkbox and select *Random Counter*.
#. Click on *add cases* and select 10-20 files (they will not be modified).
#. Check that cases have been added to the interface.
#. Click on *submit list to server* and confirm.
#. Click on the tab *my cases* and button *refresh now*. You will see the status of all your cases.
#. Increase the number of processes allowed to run.
#. While process are running, click on *refresh now* to see their status.
#. Go to the tab *my processes* to see what is happening on your computer.
#. *Random Counter* demo application has been set-up so that outputs are added to the file *gridcompute_output.txt* present in your home folder.
