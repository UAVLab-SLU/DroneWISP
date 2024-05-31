import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def plot_voxel_grid(csv_file):
    """
    Plot the voxel grid from the csv file by creating a 1-meter cube at each (x, y, z) coordinate where 'bm' equals 1.
    :param csv_file: Path to the CSV file
    :return: None
    """

    # Load the data
    df = pd.read_csv(csv_file)

    # Filter the data to include only rows where bm is 1
    filtered_df = df[df['bm'] == 1]

    # Determine the axis limits
    max_range = max(filtered_df[['x', 'y', 'z']].max() - filtered_df[['x', 'y', 'z']].min())

    mid_x = (filtered_df['x'].max() + filtered_df['x'].min()) * 0.5
    mid_y = (filtered_df['y'].max() + filtered_df['y'].min()) * 0.5
    mid_z = (filtered_df['z'].max() + filtered_df['z'].min()) * 0.5

    # Create a figure for 3 subplots (3 views)
    fig = plt.figure(figsize=(18, 7))

    def draw_cube(ax, position, size=1):
        """
        Draws a cube at the given position with the given size.
        :param ax: The axis to draw the cube on
        :param position: A tuple (x, y, z) for the cube position
        :param size: The size of the cube
        """
        x, y, z = position
        r = [0, size]
        vertices = [[x + dx, y + dy, z + dz] for dx in r for dy in r for dz in r]
        faces = [[vertices[j] for j in [0, 1, 3, 2]], [vertices[j] for j in [4, 5, 7, 6]],
                 [vertices[j] for j in [0, 1, 5, 4]], [vertices[j] for j in [2, 3, 7, 6]],
                 [vertices[j] for j in [0, 2, 6, 4]], [vertices[j] for j in [1, 3, 7, 5]]]
        ax.add_collection3d(Poly3DCollection(faces, facecolors='cyan', linewidths=1, edgecolors='r', alpha=0.25))

    # Front view (Y-Z plane, but with Y going back and Z going up)
    ax1 = fig.add_subplot(131, projection='3d')
    ax1.view_init(elev=90, azim=-90)
    for _, row in filtered_df.iterrows():
        draw_cube(ax1, (row['x'], row['z'], -row['y']))  # Y-axis values are negated to appear going back
    ax1.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
    ax1.set_ylim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
    ax1.set_zlim(-mid_y - max_range * 0.5, -mid_y + max_range * 0.5)  # Inverting limits for Y-axis
    ax1.set_xlabel('X')
    ax1.set_ylabel('Z')
    ax1.set_zlabel('Y')
    ax1.set_title('Front View')

    # Side view (Y-Z plane)
    ax2 = fig.add_subplot(132, projection='3d')
    for _, row in filtered_df.iterrows():
        draw_cube(ax2, (row['x'], row['y'], row['z']))
    ax2.view_init(elev=0, azim=0)
    ax2.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
    ax2.set_ylim(mid_y - max_range * 0.5, mid_y + max_range * 0.5)
    ax2.set_zlim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z')
    ax2.set_title('Side View')

    # Top view (X-Y plane)
    ax3 = fig.add_subplot(133, projection='3d')
    for _, row in filtered_df.iterrows():
        draw_cube(ax3, (row['x'], row['y'], row['z']))
    ax3.view_init(elev=90, azim=0)
    ax3.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
    ax3.set_ylim(mid_y - max_range * 0.5, mid_y + max_range * 0.5)
    ax3.set_zlim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_zlabel('Z')
    ax3.set_title('Top View')

    plt.show()

# Example usage
plot_voxel_grid('pinn/cesium5kTrain/1c2b0044df5fc2d5e95c0060136268309726c7e2d0e8924a5e56b84530c6448a_-13_-17/-25_25_-25_25_0_10/result_preprocessed_50.csv')

