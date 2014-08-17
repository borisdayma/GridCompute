.. include:: global.rst

Overview
========


Description
***********

GridCompute is a cross-platform tool that implements quickly distributed computing over a local grid. The applicaiton is divided into following functionalities:

- send calculations to network
- scan network for calculations to perform, execute them and send results to network
- retrieve results

Gridcompute is easy to setup and adapt to any application. Only a shared folder is required.


Applications of interest
************************

Software can be used easily if:

- Calculations performed can be divided into multiple independent calculations, even if a final step is required to merge all results
- Calculations can be started through the use of an external command line or python script
- Calculations do not interfere with user interface, ie graphic, mouse, keyboard...


Simple Workflow
***************

A very simplified workflow is represented herebelow:

|simple workflow|

More details are provided in :doc:`specifications`.
