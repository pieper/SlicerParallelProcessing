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

## Future Directions
* GUI
    * right now the gui just shows the status of processes, but it could be made more useful to show how long a process has been running or other stats like memory consumption
    * it could be useful to be able to cancel a process from the gui
    * there's currently no way to clear the output
* Logic
    * Other than the number of running processes there's no way to load balance
    * On the whole though it's good that the logic class is very clean and short
* Architecture and style
    * Could be good to break up the code into multiple files if it gets much longer
    * A helper package to pickle vtk and mrml classes would be nice independent of this
    * The process input/output shouldn't depend on only pickling, any ascii or binary data would work
    * Some more worked out examples of different use cases could help confirm that the design is workable
* Additional functionality directions
    * A process could be kept alive and exchange multiple messages (may not be worth the complexity)
    * Process invocations could be wrapped in ssh for remote execution on cluster or cloud compute resources.  The remote account would only need to have a compatible installation of Slicer (PythonSlicer) in the path.
    * Cloud computing resources (virtual machines) could even be created on the fly to perform bigger jobs
    
