import vtk
from matplotlib import pyplot as plt


def print_vtk_array_names(vtk_file):
    # Read the VTK file
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(vtk_file)
    reader.Update()

    # Get the output data
    data = reader.GetOutput()

    # Extract and print point data array names
    point_data = data.GetPointData()
    print("Point Data Arrays:")
    for i in range(point_data.GetNumberOfArrays()):
        array = point_data.GetArray(i)
        if array:
            print(array.GetName())

    # Extract and print cell data array names
    cell_data = data.GetCellData()
    print("Cell Data Arrays:")
    for i in range(cell_data.GetNumberOfArrays()):
        array = cell_data.GetArray(i)
        if array:
            print(array.GetName())

def append_marker_array(ori_vtk_file, new_vtk_file):
    # Read the VTK file
    reader = vtk.vtkUnstructuredGridReader()
    reader.SetFileName(ori_vtk_file)
    reader.Update()

    # Get the output data
    data = reader.GetOutput()

    # Get the points
    points = data.GetPoints()

    # Determine bounds
    bounds = points.GetBounds()
    x_min, x_max, y_min, y_max, z_min, z_max = bounds

    # Create a new array for markers
    marker_array = vtk.vtkIntArray()
    marker_array.SetName("marker")
    marker_array.SetNumberOfComponents(1)
    marker_array.SetNumberOfTuples(points.GetNumberOfPoints())

    # Assign marker values based on boundary conditions
    for i in range(points.GetNumberOfPoints()):
        x, y, z = points.GetPoint(i)
        if x == x_min:
            marker_array.SetValue(i, 1)  # left boundary
        elif x == x_max:
            marker_array.SetValue(i, 2)  # right boundary
        elif y == y_min:
            marker_array.SetValue(i, 3)  # lower boundary
        elif y == y_max:
            marker_array.SetValue(i, 4)  # upper boundary
        else:
            marker_array.SetValue(i, 0)  # interior point

    # Add the marker array to the point data
    data.GetPointData().AddArray(marker_array)

    # Write the updated data to a new VTK file
    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetFileName(new_vtk_file)
    writer.SetInputData(data)
    writer.Write()

def plot_marker_on_z(vtk_file, z_value):
    # Read the VTK file
    reader = vtk.vtkUnstructuredGridReader()
    reader.SetFileName(vtk_file)
    reader.Update()

    # Get the output data
    data = reader.GetOutput()

    # Get the points and marker array
    points = data.GetPoints()
    marker_array = data.GetPointData().GetArray("marker")

    if not marker_array:
        print("Marker array not found. Please run append_marker_array first.")
        return

    # Prepare data for plotting
    x_vals = []
    y_vals = []
    marker_vals = []

    for i in range(points.GetNumberOfPoints()):
        x, y, z = points.GetPoint(i)
        if z == z_value:
            x_vals.append(x)
            y_vals.append(y)
            marker_vals.append(marker_array.GetValue(i))

    if not x_vals:
        print(f"No points found at z = {z_value}")
        return

    # Create a scatter plot
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(x_vals, y_vals, c=marker_vals, cmap='viridis', marker='o')
    plt.colorbar(scatter, label='Marker Value')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title(f'Marker Values at z = {z_value}')
    plt.show()

if __name__ == "__main__":
    ori_vtk_file = "openFoamCase/VTK/openFoamCase_50.vtk"
    new_vtk_file = "updated_openFoamCase_50.vtk"
    print_vtk_array_names(ori_vtk_file)
    append_marker_array(ori_vtk_file, new_vtk_file)
    print_vtk_array_names(new_vtk_file)
    plot_marker_on_z(new_vtk_file, z_value=0)
