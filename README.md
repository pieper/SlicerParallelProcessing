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
* within your Slicer module you do the following
    * create a subclass of the Process class
    * add whatever parameters are needed in the constructor
    * override the pickledInput method to create the format your processing script expects
    * override the usePickledOutput method to consume what your script creates
    * use the ProcessingLogic class to add instances of your class and trigger them to run
    * use the completedCallback function to trigger next steps when processes have all finished
    
    * optionally block using waitForFinished (don't use this unless you really need to since it is a blocking busy loop)
## Demo

Here's what the self-test looks like.  What happens is that a dummy sphere is added to the scene 50 processes are queued, each of which applies a random offet to each of the vertices.  The machine running the test has 12 cores, so you see the processes being executed aproximately in groups of 12.  The second part shows running 5 parallel image filtering operations with different filter kernel radius values and then loading the results.  Code for these demos is in this repository.
    
[![IMAGE ALT TEXT](http://img.youtube.com/vi/lo804cRDmpQ/0.jpg)](http://www.youtube.com/watch?v=lo804cRDmpQ "What the self test looks like")

## Future Directions
* GUI
    * right now the gui just shows the status of processes, but it could be made more useful to show how long a process has been running or other stats like memory consumption
    * it could be useful to be able to cancel a process from the gui
    * there's currently no way to clear the output list of completed processes
* Logic
    * Other than limiting the number of running processes there's no way to load balance
    * On the whole though it's good that the logic class is very clean and short so we shouldn't overcomplicate it
* Architecture and style
    * Could be good to break up the code into multiple files if it gets much longer
    * A helper package to pickle vtk and mrml classes would be nice, but it should be independent of this module
    * Process input/output shouldn't be restricted to only pickling, any ascii or binary data would work
    * Some more worked out examples of different use cases could help confirm that the design is workable
* Additional functionality directions
    * A process could be kept alive and exchange multiple messages (may not be worth the complexity)
    * Process invocations could be wrapped in ssh for remote execution on cluster or cloud compute resources.  The remote account would only need to have a compatible installation of Slicer (PythonSlicer) in the path.
    * Cloud computing resources (virtual machines) could even be created on the fly to perform bigger jobs
    * The processes don't need to only operate on data that exists in Slicer, but instead the processes could download from URLs and similarly could upload results elsewhere; this could be useful in the case where Slicer's UI is used to provide interactive inputs or spot check and QC results.
