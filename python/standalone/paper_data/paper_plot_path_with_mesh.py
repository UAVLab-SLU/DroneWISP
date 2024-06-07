import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from stl import mesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

coordinates = [
    (0.0, 0.0, -0.01),
    (0.0, 0.0, 0.01),
    (0.0, 0.0, -0.04),
    (0.0, 0.0, -0.17),
    (0.0, 0.0, -0.37),
    (0.0, 0.0, -0.65),
    (0.0, 0.0, -0.99),
    (0.0, 0.0, -1.39),
    (0.0, 0.0, -1.84),
    (0.0, 0.0, -2.36),
    (0.0, -0.0, -2.9),
    (0.0, -0.01, -3.47),
    (0.0, -0.01, -4.05),
    (0.0, -0.02, -4.63),
    (0.0, -0.04, -5.15),
    (0.01, -0.05, -5.6),
    (0.04, -0.08, -5.97),
    (0.09, -0.14, -6.28),
    (0.16, -0.21, -6.53),
    (0.27, -0.31, -6.72),
    (0.4, -0.43, -6.85),
    (0.55, -0.56, -6.92),
    (0.71, -0.72, -6.92),
    (0.89, -0.87, -6.85),
    (1.09, -1.05, -6.72),
    (1.29, -1.22, -6.52),
    (1.52, -1.41, -6.27),
    (1.75, -1.61, -5.98),
    (1.99, -1.83, -5.72),
    (2.24, -2.09, -5.51),
    (2.5, -2.38, -5.34),
    (2.75, -2.68, -5.2),
    (3.01, -3.01, -5.09),
    (3.27, -3.36, -5.0),
    (3.54, -3.72, -4.94),
    (3.81, -4.1, -4.88),
    (4.08, -4.5, -4.84),
    (4.34, -4.89, -4.81),
    (4.62, -5.31, -4.79),
    (4.89, -5.73, -4.77),
    (5.16, -6.14, -4.76),
    (5.45, -6.56, -4.76),
    (5.75, -6.99, -4.76),
    (6.05, -7.39, -4.77),
    (6.39, -7.81, -4.78),
    (6.72, -8.21, -4.8),
    (7.07, -8.59, -4.82),
    (7.43, -8.95, -4.84),
    (7.83, -9.31, -4.86),
    (8.24, -9.64, -4.89),
    (8.66, -9.94, -4.91),
    (9.1, -10.22, -4.93),
    (9.54, -10.47, -4.95),
    (10.01, -10.69, -4.96),
    (10.47, -10.87, -4.97),
    (10.96, -11.03, -4.97),
    (11.46, -11.15, -4.97),
    (11.94, -11.23, -4.97),
    (12.44, -11.28, -4.97),
    (12.94, -11.29, -4.96),
    (13.43, -11.26, -4.95),
    (13.93, -11.2, -4.93),
    (14.42, -11.1, -4.92),
    (14.92, -10.97, -4.9),
    (15.4, -10.8, -4.89),
    (15.88, -10.6, -4.87),
    (16.36, -10.35, -4.85),
    (16.81, -10.09, -4.84),
    (17.26, -9.78, -4.82),
    (17.69, -9.45, -4.81),
    (18.11, -9.08, -4.8),
    (18.51, -8.69, -4.79),
    (18.89, -8.28, -4.78),
    (19.27, -7.83, -4.77),
    (19.61, -7.38, -4.77),
    (19.94, -6.89, -4.77),
    (20.25, -6.38, -4.77),
    (20.53, -5.86, -4.78),
    (20.79, -5.33, -4.78),
    (21.04, -4.76, -4.79),
    (21.25, -4.18, -4.8),
    (21.44, -3.61, -4.81),
    (21.6, -3.0, -4.82),
    (21.73, -2.41, -4.83),
    (21.83, -1.81, -4.84),
    (21.91, -1.2, -4.86),
    (21.96, -0.57, -4.87),
    (21.98, 0.04, -4.88),
    (21.97, 0.66, -4.89),
    (21.94, 1.27, -4.9),
    (21.88, 1.89, -4.91),
    (21.8, 2.5, -4.92),
    (21.69, 3.11, -4.93),
    (21.55, 3.74, -4.94),
    (21.4, 4.34, -4.94),
    (21.24, 4.91, -4.95),
    (21.05, 5.49, -4.96),
    (20.86, 6.05, -4.97),
    (20.64, 6.59, -4.98),
    (20.41, 7.13, -4.99),
    (20.15, 7.66, -5.0),
    (19.89, 8.16, -5.01),
    (19.61, 8.66, -5.02),
    (19.3, 9.13, -5.04),
    (18.98, 9.6, -5.05),
    (18.63, 10.06, -5.06),
    (18.27, 10.5, -5.07),
    (17.9, 10.91, -5.08),
    (17.5, 11.29, -5.08),
    (17.07, 11.65, -5.08),
    (16.62, 11.96, -5.07),
    (16.14, 12.25, -5.05),
    (15.66, 12.5, -5.02),
    (15.15, 12.71, -4.98),
    (14.6, 12.9, -4.94),
    (14.09, 13.03, -4.9),
    (13.58, 13.13, -4.87),
    (13.09, 13.19, -4.83),
    (12.57, 13.22, -4.79),
    (12.05, 13.22, -4.76),
    (11.53, 13.19, -4.73),
    (10.99, 13.12, -4.7),
    (10.45, 13.02, -4.68),
    (9.89, 12.89, -4.67),
    (9.24, 12.7, -4.66),
    (8.73, 12.53, -4.66),
    (8.16, 12.32, -4.66),
    (7.58, 12.08, -4.67),
    (7.02, 11.82, -4.68),
    (6.47, 11.55, -4.7),
    (5.91, 11.25, -4.72),
    (5.36, 10.94, -4.74),
    (4.82, 10.61, -4.76),
    (4.28, 10.25, -4.78),
    (3.79, 9.9, -4.8),
    (3.28, 9.52, -4.82),
    (2.8, 9.13, -4.84),
    (2.32, 8.71, -4.85),
    (1.89, 8.29, -4.87),
    (1.46, 7.84, -4.87),
    (1.06, 7.39, -4.88),
    (0.69, 6.93, -4.89),
    (0.33, 6.43, -4.89),
    (0.01, 5.94, -4.9),
    (-0.3, 5.42, -4.91),
    (-0.57, 4.9, -4.91),
    (-0.83, 4.34, -4.92),
    (-1.06, 3.79, -4.92),
    (-1.26, 3.21, -4.92),
    (-1.43, 2.65, -4.92),
    (-1.58, 2.07, -4.92),
    (-1.69, 1.51, -4.91),
    (-1.77, 0.94, -4.91),
    (-1.82, 0.31, -4.9),
    (-1.83, -0.23, -4.89),
    (-1.81, -0.77, -4.87)
]

# Convert coordinates to numpy arrays for plotting
x, y, z = zip(*coordinates)
x = np.array(x)
y = np.array(y)
z = -np.array(z)  # Invert all z values to negative

# Create the planned path on a circle centered at (8, 0, 7) with radius 8 and altitude 7
theta = np.linspace(0, 2 * np.pi, 100)
planned_path_x = 8 + 8 * np.cos(theta)
planned_path_y = 0 + 8 * np.sin(theta)
planned_path_z = np.full_like(planned_path_x, 7)


# Load the STL file
terrain_mesh = mesh.Mesh.from_file('plot_mesh.stl')

# Calculate the min and max ranges for x, y, and z coordinates
x_min, x_max = min(x.min(), planned_path_x.min()), max(x.max(), planned_path_x.max())
y_min, y_max = min(y.min(), planned_path_y.min()), max(y.max(), planned_path_y.max())
z_min, z_max = min(z.min(), planned_path_z.min()), max(z.max(), planned_path_z.max())

# Create a mask to filter the vertices within the specified ranges
mask_x = (terrain_mesh.vectors[:, :, 0] >= x_min) & (terrain_mesh.vectors[:, :, 0] <= x_max)
mask_y = (terrain_mesh.vectors[:, :, 1] >= y_min) & (terrain_mesh.vectors[:, :, 1] <= y_max)
mask_z = (terrain_mesh.vectors[:, :, 2] >= z_min) & (terrain_mesh.vectors[:, :, 2] <= z_max)

# Combine the masks
mask = mask_x & mask_y & mask_z

# Filter the vectors
filtered_vectors = terrain_mesh.vectors[np.any(mask, axis=1)]

# Create a new figure with multiple subplots
fig = plt.figure(figsize=(18, 12))

# Define different view angles
angles = [(60, 180), (60, 45), (60, 60), (90, 90)]

# Plot the path and terrain mesh from multiple angles
for i, angle in enumerate(angles, start=1):
    ax = fig.add_subplot(2, 2, i, projection='3d')

    # Plot the path
    ax.plot(x, y, z, label='Path', color='red')

    # Plot the planned path
    ax.plot(planned_path_x, planned_path_y, planned_path_z, label='Planned Path', color='blue')

    # Plot the filtered terrain mesh
    ax.add_collection3d(Poly3DCollection(filtered_vectors, alpha=0.1, facecolor='green'))

    # Set labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    # Set plot limits
    ax.set_xlim([x_min, x_max])
    ax.set_ylim([y_min, y_max])
    ax.set_zlim([z_min, z_max])

    # Set view angle
    ax.view_init(elev=angle[0], azim=angle[1])

    # Add footnote
    ax.text2D(0.05, 0.05, f'View angle: Elevation={angle[0]}, Azimuth={angle[1]}', transform=ax.transAxes)

# Add a single legend with larger font size
fig.legend(loc='upper right', fontsize=12)


# Adjust layout
plt.tight_layout()

# Show plot
plt.show()