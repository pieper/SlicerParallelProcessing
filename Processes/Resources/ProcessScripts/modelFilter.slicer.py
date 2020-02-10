import numpy
import pickle
import sys
import vtk
from vtk.util import numpy_support


pickledInput = sys.stdin.buffer.read()
input = pickle.loads(pickledInput)

polyData = vtk.vtkPolyData()
#polyData.SetPoints(input['vertexArray'])
#idArray = numpy_support.numpy_to_vtk(input['idArray'])
#polydata.GetPolys.SetCells(input['cellCount'], idArray)

# TODO: process the polydata with vtk
input['vertexArray'] += 5 * numpy.random.rand(*input['vertexArray'].shape)

output = {}
output['vertexArray'] = input['vertexArray']

sys.stdout.buffer.write(pickle.dumps(output))
