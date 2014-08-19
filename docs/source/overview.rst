.. include:: global.rst

Overview
========


Description
***********

GridCompute is a cross-platform tool that implements quickly distributed computing over a local grid.

Gridcompute is easy to setup. You just need a shared folder and a database server.
It can be adapted to any application through the use of python scripts.


Simple Workflow
***************

 The applicaiton follows the workflow:

- send calculations to the network
- scan network for calculations to perform, execute them and send results to network
- retrieve results

A very simplified workflow is represented herebelow:

|simple workflow|

For more details, refer to :doc:`specifications`.


Applications of interest
************************

Software can be used easily if:

- Calculations performed can be divided into multiple independent calculations, even if a final step is required to merge all results
- Calculations can be started through the use of an external command line or python script
- Calculations do not interfere with user interface, ie graphic, mouse, keyboard...


Interface functionalities
*************************

GridCompute interface has following functionalites:

- submit cases to the network
- specify number of processes my computer can use to process cases from the network
- modify the number of processes during execution to pause, resume or cancel processes
- monitor status of my cases
- monitor status of my processes
- create a report of all the cases from my user group present on the network
- detect failed processes and retry to launch them
- specify which machines can perform calculations depending on application required
