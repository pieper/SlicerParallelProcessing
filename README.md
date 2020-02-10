# SlicerProcesses

Slicer modules for running subprocesses to operate on data in parallel.

(Still a work in progress, but starting to be useable)

In particular, this is designed to work with python scripts that do headless processing
(no graphics or GUI).

Installation
============

Simply run slicer with these arguments:

 ./path/to/Slicer --additional-module-paths path/to/SlicerProcesses/Processes

where 'path/to' is replaced with the appropriate paths.  You could alternatively
register the path in the Module paths of the Application Settings dialog.

Usage
=====

This is designed to be a developer tool, so look at the Model and Volume tests
at the bottom of the module source code.

The basic idea is:
* you write a processing python script that does the following
    * reads binary data from stdin
    * unpickles that data to make python object (e.g. dictionary of parameters such as numpy arrays)
    * uses that data as needed
    * builds an output dictionary of results
    * pickles the output and writes the binary to stdout
* within you Slicer module you do the following
    * create a subclass of the Process class
    * add whatever parameters are needed in the constructor
    * override the pickledInput method to create the format your processing script expects
    * override the usePickledOutput method to consume what your script creates
    * use the ProcessingLogic class to add instances of your class and trigger them to run
    
## Demo

Here's what the self-test looks like.  What happens is that a dummy sphere is added to the scene 50 processes are queued, each of which applies a random offet to each of the vertices.  The machine running the test has 12 cores, so you see the processes being executed aproximately in groups of 12.  The second part shows running 5 parallel image filtering operations with different filter kernel radius values and then loading the results.  Code for these demos is in this repository.
    
[![IMAGE ALT TEXT](http://img.youtube.com/vi/lo804cRDmpQ/0.jpg)](http://www.youtube.com/watch?v=lo804cRDmpQ "What the self test looks like")
