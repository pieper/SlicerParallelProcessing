import numpy
import pickle
import sys
import vtk
from vtk.util import numpy_support


pickledInput = sys.stdin.buffer.read()
input = pickle.loads(pickledInput)

imageData = vtk.vtkImageData()
imageData.SetDimensions(*input['dimensions'])
imageData.AllocateScalars(input['type'], 1)
imageView = imageData.GetPointData().GetScalars().GetVoidPointer(0)
shape = tuple(reversed(input['dimensions']))
imageArray = numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars()).reshape(shape)
imageArray[:] = input['array']

smoother = vtk.vtkImageGaussianSmooth()
smoother.SetRadiusFactor(input['radius'])
smoother.SetInputData(imageData)
smoother.Update()

smoothedImage = smoother.GetOutputDataObject(0)
smoothedArray = numpy_support.vtk_to_numpy(smoothedImage.GetPointData().GetScalars()).reshape(shape)

output = {}
output['array'] = smoothedArray

sys.stdout.buffer.write(pickle.dumps(output))
