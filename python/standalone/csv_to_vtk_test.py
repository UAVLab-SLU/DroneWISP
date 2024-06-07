import vtk
import pandas as pd


def create_vtk_from_csv(csv_file, vtk_file):
    # Read the CSV file
    df = pd.read_csv(csv_file)

    # Determine the bounds
    x_min, x_max = df['x'].min(), df['x'].max()
    y_min, y_max = df['y'].min(), df['y'].max()
    z_min, z_max = df['z'].min(), df['z'].max()

    # Calculate the dimensions
    x_dim = int(x_max - x_min + 1)
    y_dim = int(y_max - y_min + 1)
    z_dim = int(z_max - z_min + 1)

    # Create a structured grid
    structured_grid = vtk.vtkStructuredGrid()
    structured_grid.SetDimensions(x_dim, y_dim, z_dim)

    # Create vtkPoints object
    points = vtk.vtkPoints()
    for z in range(z_dim):
        for y in range(y_dim):
            for x in range(x_dim):
                points.InsertNextPoint(x_min + x, y_min + y, z_min + z)
    structured_grid.SetPoints(points)

    # Create arrays for the data
    velocity = vtk.vtkDoubleArray()
    velocity.SetName("velocity")
    velocity.SetNumberOfComponents(3)
    velocity.SetNumberOfTuples(x_dim * y_dim * z_dim)
    velocity.FillComponent(0, 0)
    velocity.FillComponent(1, 0)
    velocity.FillComponent(2, 0)

    p_array = vtk.vtkDoubleArray()
    p_array.SetName("p")
    p_array.SetNumberOfTuples(x_dim * y_dim * z_dim)
    p_array.FillComponent(0, 0)

    k_array = vtk.vtkDoubleArray()
    k_array.SetName("k")
    k_array.SetNumberOfTuples(x_dim * y_dim * z_dim)
    k_array.FillComponent(0, 0)

    nut_array = vtk.vtkDoubleArray()
    nut_array.SetName("nut")
    nut_array.SetNumberOfTuples(x_dim * y_dim * z_dim)
    nut_array.FillComponent(0, 0)

    omega_array = vtk.vtkDoubleArray()
    omega_array.SetName("omega")
    omega_array.SetNumberOfTuples(x_dim * y_dim * z_dim)
    omega_array.FillComponent(0, 0)

    # Create a dictionary for easy indexing
    point_index = {(int(row['x']), int(row['y']), int(row['z'])): index
                   for index, row in df.iterrows()}

    for index, row in df.iterrows():
        x_idx = int(row['x'] - x_min)
        y_idx = int(row['y'] - y_min)
        z_idx = int(row['z'] - z_min)
        vtk_index = z_idx * (x_dim * y_dim) + y_idx * x_dim + x_idx
        if row['bm'] == 1:
            velocity.SetTuple3(vtk_index, 0, 0, 0)
            p_array.SetValue(vtk_index, 0)
            k_array.SetValue(vtk_index, 0)
            nut_array.SetValue(vtk_index, 0)
            omega_array.SetValue(vtk_index, 0)
        else:
            velocity.SetTuple3(vtk_index, row['u'], row['v'], row['w'])
            p_array.SetValue(vtk_index, row['p'])
            k_array.SetValue(vtk_index, row['k'])
            nut_array.SetValue(vtk_index, row['nut'])
            omega_array.SetValue(vtk_index, row['omega'])

    structured_grid.GetPointData().AddArray(velocity)
    structured_grid.GetPointData().AddArray(p_array)
    structured_grid.GetPointData().AddArray(k_array)
    structured_grid.GetPointData().AddArray(nut_array)
    structured_grid.GetPointData().AddArray(omega_array)

    # Write the structured grid to a VTK file
    writer = vtk.vtkStructuredGridWriter()
    writer.SetFileName(vtk_file)
    writer.SetInputData(structured_grid)
    writer.Write()


if __name__ == "__main__":
    csv_file = "pinn/cesium5kTrain/1c2b0044df5fc2d5e95c0060136268309726c7e2d0e8924a5e56b84530c6448a_-13_-17/-25_25_-25_25_0_10/result_preprocessed_50.csv"
    vtk_file = "updated_case.vtk"
    create_vtk_from_csv(csv_file, vtk_file)
