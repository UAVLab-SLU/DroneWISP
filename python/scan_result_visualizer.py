import os.path

import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def visualize_data_from_csv(csv_file_path):
    # Load the data
    df = pd.read_csv(csv_file_path)

    # Filter the data to include only rows where bm is 1
    filtered_df = df

    # Determine the axis limits
    max_range = max(filtered_df[['x', 'y', 'z']].max() - filtered_df[['x', 'y', 'z']].min())

    mid_x = (filtered_df['x'].max() + filtered_df['x'].min()) * 0.5
    mid_y = (filtered_df['y'].max() + filtered_df['y'].min()) * 0.5
    mid_z = (filtered_df['z'].max() + filtered_df['z'].min()) * 0.5

    # Create a figure for 3 subplots (3 views)
    fig = plt.figure(figsize=(18, 7))

    # Front view (Y-Z plane, but with Y going back and Z going up)
    ax1 = fig.add_subplot(131, projection='3d')
    ax1.view_init(elev=90, azim=-90)
    ax1.scatter(filtered_df['x'], filtered_df['z'], -filtered_df['y'], c='blue', marker='s', s=1) # Y-axis values are negated to appear going back
    ax1.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
    ax1.set_ylim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
    ax1.set_zlim(-mid_y - max_range * 0.5, -mid_y + max_range * 0.5) # Inverting limits for Y-axis
    ax1.set_xlabel('X')
    ax1.set_ylabel('Z')
    ax1.set_zlabel('Y')
    ax1.set_title('Front View')

    # Side view (Y-Z plane)
    ax2 = fig.add_subplot(132, projection='3d')
    ax2.scatter(filtered_df['x'], filtered_df['y'], filtered_df['z'], c='red', marker='s', s=1)
    ax2.view_init(elev=0, azim=0)
    ax2.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
    ax2.set_ylim(mid_y - max_range * 0.5, mid_y + max_range * 0.5)
    ax2.set_zlim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z')
    ax2.set_title('Side View')

    # Top-down view (X-Y plane)
    ax3 = fig.add_subplot(133, projection='3d')
    ax3.scatter(filtered_df['x'], filtered_df['y'], filtered_df['z'], c='green', marker='s', s=1)
    ax3.view_init(elev=90, azim=-90)
    ax3.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
    ax3.set_ylim(mid_y - max_range * 0.5, mid_y + max_range * 0.5)
    ax3.set_zlim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_zlabel('Z')
    ax3.set_title('Top-Down View')

    plt.tight_layout()
    plt.show()



csv_file_path = 'rolling_box_scan_test.csv'
visualize_data_from_csv(os.path.join(csv_file_path))
