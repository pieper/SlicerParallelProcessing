import abc
import json
import logging
import os
import pickle
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

#
# Processes
#

class Processes(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Processes"
    self.parent.categories = ["Developer Tools"]
    self.parent.dependencies = []
    self.parent.contributors = ["Steve Pieper (Isomics, Inc.)"]
    self.parent.helpText = """
This module helps you implement parallel computing processes to work on Slicer data.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Steve Pieper, Isomics, Inc. and was partially funded by This project is supported by a NSF Advances in Biological Informatics Collaborative grant to Murat Maga (ABI-1759883), Adam Summers (ABI-1759637) and Doug Boyer (ABI-1759839).
"""

#
# ProcessesWidget
#

class ProcessesWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.logic = ProcessesLogic()
    thisPath = qt.QFileInfo(__file__).path()
    self.defaultPath = os.path.join(thisPath, "Resources", "ProcessScripts", "filter.slicer.py")
    self.nodeObserverTag = None

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    self.maximumRunningProcessesSpinBox = ctk.ctkDoubleSpinBox()
    self.maximumRunningProcessesSpinBox.minimum = 1
    self.maximumRunningProcessesSpinBox.decimals = 0
    self.maximumRunningProcessesSpinBox.value = self.logic.maximumRunningProcesses
    parametersFormLayout.addRow("Maximum running processes", self.maximumRunningProcessesSpinBox)

    processesCollapsibleButton = ctk.ctkCollapsibleButton()
    processesCollapsibleButton.text = "Processes"
    self.layout.addWidget(processesCollapsibleButton)
    processesFormLayout = qt.QFormLayout(processesCollapsibleButton)

    self.statusLabel = qt.QLabel("No processes running")
    processesFormLayout.addRow(self.statusLabel)

    self.processBoxes = {}
    self.processLabels = {}
    for processState in self.logic.processStates:
        processBox = qt.QGroupBox()
        processBoxLayout = qt.QVBoxLayout(processBox)
        processBox.setTitle(processState)
        processesFormLayout.addRow(processBox)
        processLabel = qt.QLabel(processBox)
        processLabel.text = "None"
        processBoxLayout.addWidget(processLabel)
        self.processBoxes[processState] = processBox
        self.processLabels[processState] = processLabel

    self.maximumRunningProcessesSpinBox.connect("valueChanged(double)", self.onMaximumChanged)

    node = self.logic.getParameterNode()
    self.nodeObserverTag = node.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onNodeModified)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    if self.nodeObserverTag:
      node = self.logic.getParameterNode()
      node.RemoveObserver(self.nodeObserverTag)

  def onMaximumChanged(self, value):
    value = int(value)
    self.logic.setMaximumRunningProcesses(value)

  def onNodeModified(self, caller, event):
    stateJSON = self.logic.getParameterNode().GetAttribute("state")
    if stateJSON:
      self.statusLabel.text = ""
      state = json.loads(self.logic.getParameterNode().GetAttribute("state"))
      for processState in self.logic.processStates:
        labelHTML = "<ul>"
        for processName in state[processState]:
          labelHTML += f"<li>{processName}</li>"
        labelHTML += "</ul>"
        self.processLabels[processState].text = labelHTML
        self.statusLabel.text += f"{processState}: {len(state[processState])}, "
      self.statusLabel.text = self.statusLabel.text[:-2] # remove last comma and space
    else:
      self.statusLabel.text = "No state available"


#
# ProcessesLogic
#

class ProcessesLogic(ScriptedLoadableModuleLogic):

  def __init__(self, parent = None, maximumRunningProcesses=None, completedCallback=lambda : None):
    ScriptedLoadableModuleLogic.__init__(self, parent)
    if not maximumRunningProcesses:
      self.maximumRunningProcesses = os.cpu_count()
    else:
      self.maximumRunningProcesses = os.cpu_count()
    self.completedCallback = completedCallback

    self.processStates = ["Pending", "Running", "Completed", "Failed"]
    self.__initializeProcessLists()

  def __initializeProcessLists(self):
    self.processLists = {}
    for processState in self.processStates:
      self.processLists[processState] = []

  def __enter__(self):
      return self

  def __terminate(self):
    if self.processLists["Running"]:
      for process in self.processLists["Running"]:
        process.terminate()
    self.__initializeProcessLists()

  def __checkFishished(self):
    if not self.processLists["Running"] and not self.processLists["Pending"]:
      self.completedCallback()
    else:
      self.run()

  def waitForFinished(self):
    """This puts the main thread of Slicer in a tight busy loop
    waiting for the subprocesses to finish.  This allows you run background
    jobs from a synchronous (non-event driven) python script
    but be aware that it will eat up one process core and will also cause the
    application to hang until all processes complete.
    TODO: something similar to this could be implemented by doing blocking
    reads from the stdout of the processes so the main application process
    would not eat a core.
    """
    while  self.processLists["Running"]:
      self.run()
      self.processLists["Running"][0].waitForFinished()
      self.__checkFishished()

  def setMaximumRunningProcesses(self, value):
    self.maximumRunningProcesses = value

  def saveState(self):
    state = {}
    for processState in self.processStates:
      state[processState] = [process.name for process in self.processLists[processState]]
    self.getParameterNode().SetAttribute("state", json.dumps(state))

  def state(self):
    return json.loads(self.getParameterNode().GetAttribute("state"))

  def addProcess(self, process):
    self.processLists["Pending"].append(process)

  def run(self):
    while self.processLists["Pending"]:
      if len(self.processLists["Running"]) >= self.maximumRunningProcesses:
        break
      process = self.processLists["Pending"].pop()
      process.run(self)
      self.processLists["Running"].append(process)
      self.saveState()

  def onProcessFinished(self,process):
    self.processLists["Running"].remove(process)
    if process.success:
      self.processLists["Completed"].append(process)
    else:
      self.processLists["Failed"].append(process)
    self.saveState()
    self.__checkFishished()

class Process(qt.QProcess):
  """
  """

  QProcessStateNames = {qt.QProcess.NotRunning: 'NotRunning', qt.QProcess.Starting: 'Starting', qt.QProcess.Running: 'Running'}
  QProcessErrorNames = {qt.QProcess.FailedToStart: 'FailedToStart', qt.QProcess.Crashed: 'Crashed', qt.QProcess.Timedout: 'Timedout',
    qt.QProcess.WriteError: 'WriteError', qt.QProcess.ReadError: 'ReadError', qt.QProcess.UnknownError: 'UnknownError'}
  QProcessExitStatusNames = {qt.QProcess.NormalExit: 'NormalExit', qt.QProcess.CrashExit: 'CrashExit'}

  def __init__(self, scriptPath):
    super().__init__()
    self.name = "Process"
    self.processState = "Pending"
    self.scriptPath = scriptPath
    self.success = True

  def run(self, logic):
    self.connect('stateChanged(QProcess::ProcessState)', self.onStateChanged)
    self.connect('started()', self.onStarted)
    self.finishedSlot = lambda exitCode, exitStatus : self.onFinished(logic, exitCode, exitStatus)
    self.connect('finished(int,QProcess::ExitStatus)', self.finishedSlot)
    self.start("PythonSlicer", [self.scriptPath,])

  def onStateChanged(self, newState):
    msg = f'{self.name}: state: {Process.QProcessStateNames[self.state()]}'

    # qt.QProcess.UnknownError usually means that there is no error, therefore
    # to prevent polluting the logs and confusint users, we don't print UnknownError.
    if self.error() != qt.QProcess.UnknownError:
      msg += f', last error: {Process.QProcessErrorNames[self.error()]}'

    logging.info(msg)

  def onStarted(self):
    """ This method will write the prepareProcessInput to the stdin
    of the process.  If you want to debug your processing script
    outside of this module, you can add some code like this:

      with open("/tmp/inputToProcess", "w") as fp:
        fp.buffer.write(self.prepareProcessInput())
      print("PythonSlicer", [self.scriptPath,])

    and then run the PythonSlicer executable with the input redirected
    from the tmp file.
    """
    logging.info(f"{self.name}: writing input")
    self.write(self.prepareProcessInput())
    self.closeWriteChannel()

  def onFinished(self, logic, exitCode, exitStatus):
    try:
      logging.info(f'{self.name}: finished, exit code: {exitCode}, exit status: {Process.QProcessExitStatusNames[exitStatus]}')
      stdout = self.readAllStandardOutput()
      stderr = self.readAllStandardError()
      if stderr:
        logging.error(f'{self.name}: error output:\n---\n{stderr.data().decode()}---')
      self.useProcessOutput(stdout.data())
    except:
      self.success = False
      raise
    finally:
      logic.onProcessFinished(self)
    self.disconnect('stateChanged(QProcess::ProcessState)', self.onStateChanged)
    self.disconnect('started()', self.onStarted)
    self.disconnect('finished(int,QProcess::ExitStatus)', self.finishedSlot)

  @abc.abstractmethod
  def prepareProcessInput(self):
    pass

  @abc.abstractmethod
  def useProcessOutput(self, processOutput):
    pass


class VolumeFilterProcess(Process):
  """This is an example of using a process to operate on volume data
  """

  def __init__(self, scriptPath, volumeNode, radius):
    Process.__init__(self, scriptPath)
    self.volumeNode = volumeNode
    self.radius = radius
    self.name = f"Filter {radius}"

  def prepareProcessInput(self):
    input = {}
    input['array'] = slicer.util.arrayFromVolume(self.volumeNode)
    input['spacing'] = self.volumeNode.GetSpacing()
    input['dimensions'] = self.volumeNode.GetImageData().GetDimensions()
    input['type'] = self.volumeNode.GetImageData().GetScalarType()
    input['radius'] = self.radius
    return pickle.dumps(input)

  def useProcessOutput(self, processOutput):
    output = pickle.loads(processOutput)
    ijkToRAS = vtk.vtkMatrix4x4()
    self.volumeNode.GetIJKToRASMatrix(ijkToRAS)
    slicer.util.addVolumeFromArray(output['array'], ijkToRAS, self.name)
    import CompareVolumes
    CompareVolumes.CompareVolumesLogic().viewersPerVolume()


class ModelFilterProcess(Process):
  """This is an example of running a process to operate on model data"""

  def __init__(self, scriptPath, modelNode, iteration):
    Process.__init__(self, scriptPath)
    self.modelNode = modelNode
    self.name = f"Filter {modelNode.GetName()}-{iteration}"

  def arrayFromModelPolyIds(self, modelNode):
    from vtk.util.numpy_support import vtk_to_numpy
    arrayVtk = modelNode.GetPolyData().GetPolys().GetData()
    narray = vtk_to_numpy(arrayVtk)
    return narray

  def prepareProcessInput(self):
    if hasattr(slicer.util, "arrayFromModelPolyIds"):
      arrayFromModelPolyIds = slicer.util.arrayFromModelPolyIds
    else:
      arrayFromModelPolyIds = self.arrayFromModelPolyIds
    input = {}
    input['vertexArray'] = slicer.util.arrayFromModelPoints(self.modelNode)
    input['cellCount'] = self.modelNode.GetPolyData().GetPolys().GetNumberOfCells()
    input['idArray'] = arrayFromModelPolyIds(self.modelNode)
    return pickle.dumps(input)

  def useProcessOutput(self, processOutput):
    output = pickle.loads(processOutput)
    vertexArray = slicer.util.arrayFromModelPoints(self.modelNode)
    vertexArray[:] = output['vertexArray']
    slicer.util.arrayFromModelPointsModified(self.modelNode)


class ProcessesTest(ScriptedLoadableModuleTest):

  def setUp(self):
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    self.setUp()
    self.test_ModelProcesses()

  def test_ModelProcesses(self):

    self.delayDisplay("Starting the Model test")

    layoutManager = slicer.app.layoutManager()
    layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)

    modelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
    modelNode.CreateDefaultDisplayNodes()

    sphereSource = vtk.vtkSphereSource()
    sphereSource.SetRadius(10)
    sphereSource.SetThetaResolution(50)
    sphereSource.SetPhiResolution(50)
    sphereSource.Update()
    modelNode.SetAndObservePolyData(sphereSource.GetOutputDataObject(0))

    def onProcessesCompleted(testClass):
      testClass.assertEqual(len(logic.state()['Completed']), 50)
      testClass.assertEqual(len(logic.state()['Failed']), 0)
      testClass.delayDisplay('Test passed!')
      # when first test finishes, run second test
      testClass.setUp()
      testClass.test_VolumeProcesses()

    logic = ProcessesLogic(completedCallback=lambda : onProcessesCompleted(self))
    thisPath = qt.QFileInfo(__file__).path()
    scriptPath = os.path.join(thisPath, "Resources", "ProcessScripts", "modelFilter.slicer.py")

    for iteration in range(50):
      filterProcess = ModelFilterProcess(scriptPath, modelNode, iteration)
      logic.addProcess(filterProcess)

    logic.run()


  def test_VolumeProcesses(self):

    self.delayDisplay("Starting the Volume test")

    import SampleData
    volumeNode = SampleData.downloadSample("MRHead")

    def onProcessesCompleted(testClass):
      # when test finishes, we succeeded!
      testClass.assertEqual(len(logic.state()['Completed']), 5)
      testClass.assertEqual(len(logic.state()['Failed']), 0)
      testClass.delayDisplay('Test passed!')

    logic = ProcessesLogic(completedCallback=lambda : onProcessesCompleted(self))
    thisPath = qt.QFileInfo(__file__).path()
    scriptPath = os.path.join(thisPath, "Resources", "ProcessScripts", "volumeFilter.slicer.py")

    for radius in range(5):
      filterProcess = VolumeFilterProcess(scriptPath, volumeNode, radius*5)
      logic.addProcess(filterProcess)

    logic.run()

    logic.waitForFinished()  # Optional
