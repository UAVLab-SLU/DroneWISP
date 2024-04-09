import os.path

import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def visualize_data_from_csv(csv_file_path):
    # Load the data

    df = pd.read_csv(csv_file_path)

    # Filter the data to include only rows where bm is 1
    filtered_df = df[df['bm'] == 0]

    # Create a figure for 3 subplots (3 views)
    fig = plt.figure(figsize=(18, 6))

    # Front view (X-Z plane)
    ax1 = fig.add_subplot(131, projection='3d')
    ax1.scatter(filtered_df['y'], filtered_df['x'], filtered_df['z'], c='blue', marker='o', s=1)
    ax1.view_init(elev=20, azim=-90)
    ax1.set_xlabel('Y')
    ax1.set_ylabel('X')
    ax1.set_zlabel('Z')
    ax1.set_title('View from X-axis')

    # Side view (Y-Z plane)
    ax2 = fig.add_subplot(132, projection='3d')
    ax2.scatter(filtered_df['x'], filtered_df['y'], filtered_df['z'], c='red', marker='o', s=1)
    ax2.view_init(elev=20, azim=0)
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z')
    ax2.set_title('View from Y-axis')

    # Z view top-down (X-Y plane)
    ax3 = fig.add_subplot(133, projection='3d')
    ax3.scatter(filtered_df['x'], filtered_df['y'], filtered_df['z'], c='green', marker='o', s=1)
    ax3.view_init(elev=90, azim=-90)
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_zlabel('Z')
    ax3.set_title('View from Z-axis')

    plt.tight_layout()
    plt.show()


# Assuming the CSV file is named 'result_preprocessed_time.csv' and located in the current directory
time = 50
open_foam_case_root = "../5k_training_dataset/-25_0_-100_-75_0_10"
csv_file_path = 'result_preprocessed_' + str(time) + '.csv'
visualize_data_from_csv(os.path.join(open_foam_case_root, csv_file_path))
