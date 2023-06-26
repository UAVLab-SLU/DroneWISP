# import paraview.simple
import os

output_dir = "csv"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

import vtk
from vtk.numpy_interface import dataset_adapter as dsa
import numpy as np

#PolyDataReader must be modified depending on the type of the Legacy VTK input type
reader = vtk.vtkPolyDataReader()
reader.SetFileName("cylinder.vtk")
reader.ReadAllFieldsOn()
reader.Update()
vtk_data = reader.GetOutput()

vtk_dataset_adapter = dsa.WrapDataObject(vtk_data)

coords = vtk_dataset_adapter.GetPoints()
density = vtk_dataset_adapter.PointData['density']

data_export = np.column_stack((coords,density))

header = "X Y Z density"
np.savetxt("output3.csv", data_export, header = header)