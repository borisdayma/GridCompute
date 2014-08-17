Development
===========

This section details how to use source code for developers. You can get latest code and binaries at:
http://github.com/borisd13/GridCompute


Requirements
************

The following is required to use the source code:

* `python version 3.4.0 or superior <https://www.python.org/>`_
* tkinter (should be included in python installation)
* pip for python3 (should be included in python installation)
* `pymongo version 2.7.1 or superior <http://api.mongodb.org/python/current/>`_
* `psutil version 2.1.1 or superior <https://github.com/giampaolo/psutil>`_


Install requirements on Ubuntu
------------------------------

Enter below commands in prompt:

>>> sudo apt-get install python3-pip
>>> sudo pip3 install pymongo
>>> sudo pip3 install psutil
>>> sudo apt-get install python3-tk


Install requirements on Windows
-------------------------------

Follow below instructions:

#. `download and install python 3.4.1 (64 bit version) <https://www.python.org/>`_. Make sure to enable "Add python.exe to Path"
#. `download and install pymongo <https://pypi.python.org/pypi/pymongo/>`_
#. `download and install psutil <https://pypi.python.org/pypi/psutil/2.1.1>`_


Build application
*****************

GridCompute is meant to be run easily on computers that don't have any installation on python. This is achieved by creating binaries of the application with the help of `cx_Freeze <http://cx-freeze.sourceforge.net/>`_.

.. note:: Building the application is not required for executing the program.

To build the application:

#. Use the OS you plan to build the application for
#. Install `cx_Freeze from source <https://bitbucket.org/anthony_tuininga/cx_freeze/src>`_
     | **Note:**
     | On Ubuntu, you might need to apply fix for `issue 32 <https://bitbucket.org/anthony_tuininga/cx_freeze/issue/32/cant-compile-cx_freeze-in-ubuntu-1304#comment-11181579>`_
     | On Windows, you may have to install Visual Studio C++ 2010
#. Go to main folder of GridCompute source code and run ``python setup.py build``
     **Note:** On Ubuntu, you will also need to apply fix for `issue 95 <https://bitbucket.org/anthony_tuininga/cx_freeze/issue/95/>`_


Build documentation
*******************

Documentation is generated through the use of `sphinx <http://sphinx-doc.org/>`_. To build documentation:

* Install sphinx with pip
* Go to *docs* folder and run ``make html``


Execute application
*******************

From source, run **python 3** on *main.py*.

From executable, just run *GridCompute* executable.
